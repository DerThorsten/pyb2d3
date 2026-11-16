"""Helpers shared by the batch API samples (batch_*.py)."""

import numpy as np

import pyb2d3 as b2d


def hsv_colors(hue, saturation=0.75, value=0.95):
    """Vectorized HSV -> 0xRRGGBB colors (hue in [0, 1))."""
    hue = np.asarray(hue, dtype=np.float64) % 1.0
    saturation = np.broadcast_to(saturation, hue.shape)
    value = np.broadcast_to(value, hue.shape)
    sector = np.floor(hue * 6.0).astype(int) % 6
    f = hue * 6.0 - np.floor(hue * 6.0)
    p = value * (1.0 - saturation)
    q = value * (1.0 - f * saturation)
    t = value * (1.0 - (1.0 - f) * saturation)
    r = np.choose(sector, [value, q, p, p, t, value])
    g = np.choose(sector, [t, value, value, q, p, p])
    b = np.choose(sector, [p, p, t, value, value, q])
    rgb = (np.stack([r, g, b], axis=-1) * 255).round().astype(np.uint32)
    return (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]


def create_circles(
    world, positions, radius, colors=None, density=1.0, friction=0.2, restitution=0.0, **body_kwargs
):
    """One dynamic circle body per row of `positions`, returned as a `b2d.Bodies` batch.

    `radius` and `colors` are a single value or one value per body. Creating bodies is
    a python loop, but only once (frequent emission: `ParticlePool`).
    """
    n = len(positions)
    radii = np.broadcast_to(np.asarray(radius, dtype=np.float64), (n,))
    colors = np.broadcast_to(np.asarray(0 if colors is None else colors, dtype=np.uint32), (n,))
    bodies = b2d.Bodies()
    for (x, y), r, color in zip(positions, radii, colors):
        body = world.create_dynamic_body(position=(float(x), float(y)), **body_kwargs)
        material = b2d.surface_material(
            friction=friction, restitution=restitution, custom_color=int(color)
        )
        body.create_shape(
            b2d.shape_def(density=density, material=material), b2d.circle(radius=float(r))
        )
        bodies.append(body)
    return bodies


def unit_and_length(vectors, eps=1e-6):
    """Row-wise unit vectors and lengths of an (n, 2) array."""
    length = np.linalg.norm(vectors, axis=1)
    return vectors / np.maximum(length, eps)[:, None], length


def perpendicular(vectors):
    """Rotate every row of an (n, 2) array by +90 degrees."""
    return np.stack([-vectors[:, 1], vectors[:, 0]], axis=1)


class Ema:
    """Exponential moving average, for timings shown on screen."""

    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.value = None

    def __call__(self, sample):
        self.value = (
            sample if self.value is None else (1.0 - self.alpha) * self.value + self.alpha * sample
        )
        return self.value


# ---- neighbor search ------------------------------------------------------------------------

# cell offsets that visit every pair of neighboring cells once: same, right, up-left, up, up-right
_HALF_STENCIL = ((0, 0), (1, 0), (-1, 1), (0, 1), (1, 1))


def neighbor_pairs(positions, radius):
    """All pairs closer than `radius`, with a uniform grid (cell size `radius`):
    O(n) for evenly spread points instead of the n^2 of all pairs.

    Returns (i, j, delta, distance): index arrays with i != j (each pair once),
    delta = positions[j] - positions[i] and its length.
    """
    pos = np.asarray(positions, dtype=np.float64)
    if len(pos) < 2:
        empty = np.zeros(0, dtype=np.int64)
        return empty, empty, np.zeros((0, 2)), np.zeros(0)
    cells = np.floor(pos / radius).astype(np.int64)
    cells -= cells.min(axis=0) - 1  # >= 1: the -1 neighbor column stays >= 0
    width = int(cells[:, 0].max()) + 2
    key = cells[:, 1] * width + cells[:, 0]
    order = np.argsort(key, kind="stable")
    keys, start, count = np.unique(key[order], return_index=True, return_counts=True)

    pair_i, pair_j = [], []
    for dx, dy in _HALF_STENCIL:
        other = np.searchsorted(keys, keys + dy * width + dx)
        other = np.minimum(other, len(keys) - 1)
        found = keys[other] == keys + dy * width + dx
        a_cells, b_cells = np.flatnonzero(found), other[found]
        ca, cb = count[a_cells], count[b_cells]
        total = ca * cb
        if total.sum() == 0:
            continue
        # every member of cell a with every member of cell b
        pair_of = np.repeat(np.arange(len(a_cells)), total)
        within = np.arange(total.sum()) - np.repeat(np.cumsum(total) - total, total)
        ia = start[a_cells][pair_of] + within // cb[pair_of]
        ib = start[b_cells][pair_of] + within % cb[pair_of]
        if (dx, dy) == (0, 0):
            keep = ia < ib  # within a cell: each pair once, no self pairs
            ia, ib = ia[keep], ib[keep]
        pair_i.append(order[ia])
        pair_j.append(order[ib])

    i = np.concatenate(pair_i)
    j = np.concatenate(pair_j)
    delta = pos[j] - pos[i]
    distance = np.sqrt(np.einsum("ij,ij->i", delta, delta))
    close = distance < radius
    return i[close], j[close], delta[close], distance[close]


def pair_sum(n, i, j, values):
    """Per-body sums of pairwise (n_pairs, 2) `values`: + on body i, - on body j
    (equal and opposite forces)."""
    out = np.zeros((n, 2))
    for axis in range(2):
        out[:, axis] = np.bincount(i, values[:, axis], n) - np.bincount(j, values[:, axis], n)
    return out


# ---- recycled particles ---------------------------------------------------------------------


class ParticlePool:
    """A fixed pool of circle bodies: parked ones are disabled, `emit` enables and
    launches some (the oldest flying ones when the pool runs dry), `park` disables
    them again. Creating bodies is slow, enabling / moving them is a batch call."""

    def __init__(
        self,
        world,
        size,
        radius,
        color,
        parking=(0.0, -500.0),
        density=1.0,
        friction=0.2,
        restitution=0.1,
        **body_kwargs,
    ):
        positions = np.tile(np.asarray(parking, dtype=np.float64), (size, 1))
        self.bodies = create_circles(
            world,
            positions,
            radius,
            colors=color,
            density=density,
            friction=friction,
            restitution=restitution,
            **body_kwargs,
        )
        self.bodies.enabled = False
        self.active = np.zeros(size, dtype=bool)
        self.age = np.zeros(size)
        self._shapes = None

    def __len__(self):
        return len(self.bodies)

    @property
    def shapes(self):
        """the circle shape of every body (for per-particle colors)"""
        if self._shapes is None:
            self._shapes = [body.shapes[0] for body in self.bodies]
        return self._shapes

    def step(self, dt):
        self.age[self.active] += dt

    def emit(self, positions, velocities):
        """launch len(positions) particles, returns their indices"""
        k = len(positions)
        if k == 0:
            return np.zeros(0, dtype=np.int64)
        free = np.flatnonzero(~self.active)[:k]
        if len(free) < k:
            flying = np.flatnonzero(self.active)
            need = k - len(free)
            oldest = flying[np.argpartition(-self.age[flying], need - 1)[:need]]
            free = np.concatenate([free, oldest])
        batch = self.bodies[free]
        batch.enabled = True  # enable first: a disabled body ignores velocity changes
        batch.set_transform(np.asarray(positions, dtype=np.float64), (1.0, 0.0))
        batch.linear_velocity = np.asarray(velocities, dtype=np.float64)
        batch.angular_velocity = 0.0
        self.active[free] = True
        self.age[free] = 0.0
        return free

    def park(self, mask):
        """disable the particles of the boolean `mask` (only active ones count)"""
        mask = mask & self.active
        if mask.any():
            self.bodies[mask].enabled = False
            self.active &= ~mask

    def destroy(self):
        self.bodies.destroy()
        self.bodies = b2d.Bodies()


# ---- shaking ----------------------------------------------------------------------------


class Shaker:
    """Moves a kinematic body along a sine around its start pose (shaking boxes,
    earthquakes): call `step(time, dt)` once per step."""

    def __init__(self, body, axis=(1.0, 0.0), amplitude=0.5, frequency=2.0):
        self.body = body
        position = body.position
        self.base = np.array([position.x, position.y], dtype=np.float64)
        self.rotation = body.rotation
        self.axis = np.asarray(axis, dtype=np.float64) / np.linalg.norm(axis)
        self.amplitude = amplitude
        self.frequency = frequency

    def offset(self, time):
        return self.amplitude * np.sin(2.0 * np.pi * self.frequency * time) * self.axis

    def step(self, time, dt):
        target = self.base + tuple(self.offset(time + dt))
        self.body.set_target_transform(
            b2d.transform(p=tuple(target), q=self.rotation), dt, wake=True
        )


# ---- plots drawn with debug draw ----------------------------------------------------------------


def draw_curve(debug_draw, points, color):
    """a polyline through (n, 2) points"""
    points = np.asarray(points, dtype=np.float64)
    for p, q in zip(points[:-1], points[1:]):
        debug_draw.draw_segment(tuple(p), tuple(q), color)


def draw_histogram(debug_draw, origin, size, counts, color, reference=None, reference_color=None):
    """bars of `counts` into the box `origin` + `size`; optional `reference`
    curve (same scale as counts) drawn on top"""
    ox, oy = origin
    w, h = size
    counts = np.asarray(counts, dtype=np.float64)
    top = max(float(counts.max()), float(np.max(reference)) if reference is not None else 0.0, 1.0)
    bar = w / len(counts)
    for k, c in enumerate(counts):
        x0 = ox + k * bar
        y1 = oy + h * c / top
        draw_curve(debug_draw, [(x0, oy), (x0, y1), (x0 + bar, y1), (x0 + bar, oy)], color)
    if reference is not None:
        x = ox + bar * (np.arange(len(reference)) + 0.5)
        draw_curve(
            debug_draw,
            np.stack([x, oy + h * np.asarray(reference) / top], axis=1),
            reference_color or b2d.HexColor.White,
        )
