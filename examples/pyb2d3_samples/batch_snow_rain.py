"""Snow globe and rain: hundreds of slow flakes in a globe you shake, or a rain
shower over moving umbrellas (recycled drops, numpy masks + batch calls)."""

import math

import numpy as np

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase, widgets

from .batch_common import ParticlePool, Shaker, create_circles, destroy_bodies, hsv_colors

MODES = ["snow globe", "rain"]


class BatchSnowRain(SampleBase):
    """Two weathers. Snow globe: flakes sink slowly through the liquid (high drag)
    and settle on a little village; shake the globe and they swirl up again.
    Rain: a shower of recycled drops falls on umbrellas walking to and fro.

    Keys: space shakes the globe.
    Mouse: hold to stir the flakes (snow) / drag the umbrellas (rain).
    Sliders: rain rate and wind (rain), flutter (snow).
    Hint: all flakes / drops move with one batch call per step; the drops come
    from a fixed pool, parked drops are recycled for new ones.
    """

    globe_center = (0.0, 6.0)
    globe_radius = 5.0
    ground = 0.0

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings.set_gravity((0, -10)))
        self.mode = MODES[0]
        self.rate = 300.0  # drops / s
        self.wind = 2.0
        self.flutter = 3.0
        self.rng = np.random.default_rng(17)
        self.time = 0.0
        self.scene = []  # static / kinematic bodies of the current mode
        self.flakes = b2d.Bodies()
        self.pool = None
        self.stir = None
        self.shake_until = -1.0
        self.splashes = []  # (position, time) of drops hitting the ground
        self.build()
        for widget in (
            widgets.RadioButtons("weather", MODES, self.mode, self.set_mode),
            widgets.Button("shake (space)", self.shake),
            widgets.FloatSlider("flutter", 0.0, 10.0, 0.25, self.flutter, self.set_flutter),
            widgets.FloatSlider("rain (drops/s)", 20.0, 800.0, 10.0, self.rate, self.set_rate),
            widgets.FloatSlider("wind", -8.0, 8.0, 0.25, self.wind, self.set_wind),
        ):
            self.frontend.add_widget(widget)

    def aabb(self):
        return b2d.aabb(lower_bound=(-12.0, -1.0), upper_bound=(12.0, 13.0))

    # ---- scenes -------------------------------------------------------------------------

    def clear(self):
        """remove everything of the current mode"""
        destroy_bodies(self, self.flakes)
        self.flakes = b2d.Bodies()
        if self.pool is not None:
            self.pool.destroy(self)
            self.pool = None
        for body in self.scene:
            body.destroy()
        self.scene = []
        self.shakers = []
        self.splashes = []

    def build(self):
        """the scene of the current mode"""
        self.clear()
        if self.mode == "snow globe":
            self.build_globe()
        else:
            self.build_rain()

    def build_globe(self):
        """a kinematic globe (a ring of segments + a village inside) full of flakes"""
        cx, cy = self.globe_center
        r = self.globe_radius
        globe = self.world.create_kinematic_body(position=(cx, cy), enable_sleep=False)
        glass = b2d.shape_def(material=b2d.surface_material(friction=0.2, custom_color=b2d.HexColor.LightSkyBlue))
        n = 48
        angles = np.linspace(0.0, 2.0 * math.pi, n + 1)
        ring = np.stack([r * np.cos(angles), r * np.sin(angles)], axis=1)
        # thick glass (capsules just outside the radius): thin segments let fast
        # flakes of a shaken globe tunnel out
        ring *= (r + 0.15) / r
        for p, q in zip(ring[:-1], ring[1:]):
            globe.create_shape(glass, b2d.capsule(tuple(p), tuple(q), 0.15))
        # the village: a snow field, two houses, a fir tree (part of the globe)
        wood = b2d.shape_def(material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.SaddleBrown))
        roof = b2d.shape_def(material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.Firebrick))
        fir = b2d.shape_def(material=b2d.surface_material(friction=0.8, custom_color=b2d.HexColor.ForestGreen))
        floor = -0.6 * r
        globe.create_shape(wood, b2d.box(0.8 * r, 0.15, center=(0.0, floor - 0.15)))
        for x, w, h in ((-2.0, 0.8, 0.7), (1.2, 0.6, 0.55)):
            globe.create_shape(wood, b2d.box(w, h, center=(x, floor + h)))
            globe.create_shape(roof, b2d.polygon(points=[(x - w - 0.2, floor + 2 * h), (x + w + 0.2, floor + 2 * h),
                                                         (x, floor + 2 * h + 0.9 * w)]))
        globe.create_shape(fir, b2d.polygon(points=[(3.0, floor), (3.9, floor), (3.45, floor + 2.4)]))
        # the stand
        stand = self.world.create_static_body(position=(cx, cy - r - 0.6))
        stand.create_shape(wood, b2d.box(3.0, 0.6))
        self.scene = [globe, stand]
        self.globe = globe
        self.globe_shaker = Shaker(globe, axis=(1.0, 0.35), amplitude=0.45, frequency=2.5)
        # flakes: a jittered disc inside the globe
        count = 800
        radius = r * np.sqrt(self.rng.uniform(0.0, 0.8, count))
        angle = self.rng.uniform(0.0, 2.0 * math.pi, count)
        positions = np.stack([cx + radius * np.cos(angle), cy + radius * np.sin(angle)], axis=1)
        positions[:, 1] = np.maximum(positions[:, 1], cy + floor + 1.5)
        whites = hsv_colors(np.full(count, 0.6), self.rng.uniform(0.0, 0.12, count), 1.0)
        self.flakes = create_circles(self.world, positions, self.rng.uniform(0.04, 0.08, count), colors=whites,
                                     density=0.5, friction=0.6, linear_damping=10.0, enable_sleep=False)

    def build_rain(self):
        """ground, umbrellas walking to and fro, a pool of drops"""
        ground = self.world.create_static_body(position=(0.0, self.ground))
        ground.create_shape(b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.DimGray)),
                            b2d.box(14.0, 0.25, center=(0.0, -0.25)))
        self.scene = [ground]
        self.shakers = []
        cloth = [b2d.HexColor.Crimson, b2d.HexColor.Gold, b2d.HexColor.MediumSeaGreen]
        for k, (x, y, period) in enumerate(((-6.0, 3.2, 7.0), (0.5, 4.0, 9.5), (6.0, 3.5, 6.0))):
            umbrella = self.world.create_kinematic_body(position=(x, y), enable_sleep=False)
            canopy = b2d.shape_def(material=b2d.surface_material(friction=0.2, custom_color=cloth[k]))
            angles = np.linspace(math.radians(15), math.radians(165), 12)
            arc = np.stack([1.8 * np.cos(angles), 0.8 * np.sin(angles)], axis=1)
            # thick canopy: a drop falls ~0.2 m per step and kinematic bodies get
            # no continuous collision, a thin canopy would let drops tunnel through
            for p, q in zip(arc[:-1], arc[1:]):
                umbrella.create_shape(canopy, b2d.capsule(tuple(p), tuple(q), 0.16))
            handle = b2d.shape_def(material=b2d.surface_material(custom_color=b2d.HexColor.Black))
            umbrella.create_shape(handle, b2d.capsule((0.0, 0.8), (0.0, -2.0), 0.04))
            self.scene.append(umbrella)
            self.shakers.append(Shaker(umbrella, axis=(1.0, 0.0), amplitude=2.5, frequency=1.0 / period))
        no_drop_contacts = b2d.make_filter(group_index=-1)  # drops pass through each other
        self.pool = ParticlePool(self.world, 1200, 0.045, int(b2d.HexColor.LightSkyBlue.value), parking=(0.0, -50.0),
                                 restitution=0.0, friction=0.0, enable_sleep=False)
        for shape in self.pool.shapes:
            shape.filter = no_drop_contacts
        self.budget = 0.0

    # ---- controls -------------------------------------------------------------------------

    def set_mode(self, value):
        self.mode = value
        self.build()

    def set_rate(self, value):
        self.rate = value

    def set_wind(self, value):
        self.wind = value

    def set_flutter(self, value):
        self.flutter = value

    def shake(self):
        """shake the globe for a moment"""
        if self.mode == "snow globe":
            self.shake_until = self.time + 1.6

    def on_key_down(self, event):
        if event.key == "space":
            self.shake()

    def on_mouse_down(self, event):
        """snow: stir (no body dragging inside the globe); rain: drag as usual"""
        if self.mode == "snow globe":
            self.stir = np.array(event.world_position, dtype=np.float64)
        else:
            super().on_mouse_down(event)

    def on_mouse_move(self, event):
        if self.stir is not None:
            self.stir = np.array(event.world_position, dtype=np.float64)
        else:
            super().on_mouse_move(event)

    def on_mouse_up(self, event):
        self.stir = None
        super().on_mouse_up(event)

    def on_mouse_leave(self, event):
        self.stir = None
        super().on_mouse_leave(event)

    # ---- simulation -----------------------------------------------------------------------

    def pre_update(self, dt):
        if self.mode == "snow globe":
            self.update_snow(dt)
        else:
            self.update_rain(dt)
        self.time += dt

    def update_snow(self, dt):
        """move the globe (shaking or at rest), flutter + stir + the liquid
        sloshing in a shaken globe: one batch call for all flakes"""
        shaking = self.time < self.shake_until
        if shaking:
            self.globe_shaker.step(self.time, dt)
        else:
            base = self.globe_shaker.base
            self.globe.set_target_transform(b2d.transform(p=(float(base[0]), float(base[1]))), dt, wake=False)
        n = len(self.flakes)
        accel = self.rng.normal(0.0, self.flutter, (n, 2))  # little eddies
        if shaking:
            # the liquid of a shaken globe swirls: strong random eddies + an upward kick
            accel += self.rng.normal(0.0, 40.0, (n, 2)) + (0.0, 25.0)
        if self.stir is not None:
            offset = self.flakes.position - self.stir
            distance = np.linalg.norm(offset, axis=1)
            near = np.clip(1.0 - distance / 2.5, 0.0, 1.0)
            swirl = np.stack([-offset[:, 1], offset[:, 0]], axis=1) / np.maximum(distance, 0.2)[:, None]
            accel += 60.0 * near[:, None] * (swirl + np.array([0.0, 0.5]))  # swirl + a little lift
        self.flakes.apply_force_to_center(self.flakes.mass[:, None] * accel)

    def update_rain(self, dt):
        """umbrellas walk, new drops at the top, drops on the ground are parked"""
        for shaker in self.shakers:
            shaker.step(self.time, dt)
        pool = self.pool
        pool.step(dt)
        positions = pool.bodies.position
        landed = pool.active & (positions[:, 1] < self.ground + 0.12)
        expired = pool.active & ((pool.age > 6.0) | (np.abs(positions[:, 0]) > 16.0))
        if landed.any():
            self.splashes.extend((tuple(p), self.time) for p in positions[landed])
        pool.park(landed | expired)
        self.splashes = [s for s in self.splashes if self.time - s[1] < 0.25][-400:]
        self.budget += self.rate * dt
        k = int(self.budget)
        if k:
            self.budget -= k
            start = np.stack([self.rng.uniform(-14.0, 14.0, k) - 0.6 * self.wind, np.full(k, 12.5)], axis=1)
            velocity = np.stack([np.full(k, self.wind), self.rng.uniform(-12.0, -9.0, k)], axis=1)
            pool.emit(start, velocity)
        flying = pool.bodies[pool.active]
        if len(flying):
            # air drag towards the wind (one batch call for all drops in flight)
            relative = np.array([self.wind, 0.0]) - flying.linear_velocity
            relative[:, 1] = 0.0
            flying.apply_force_to_center(0.8 * flying.mass[:, None] * relative)
        self.landed = int(np.count_nonzero(landed))

    # ---- drawing --------------------------------------------------------------------------

    def post_debug_draw(self):
        dd = self.debug_draw
        if self.mode == "snow globe":
            speed = self.flakes.speed
            floating = int(np.count_nonzero(speed > 0.15))
            state = "shaking" if self.time < self.shake_until else "settling"
            outside = np.linalg.norm(self.flakes.position - self.globe_shaker.base, axis=1) > self.globe_radius + 0.5
            text = f"{len(self.flakes)} flakes, {floating} floating ({state})"
            if outside.any():
                text += f", {int(outside.sum())} outside the globe"
        else:
            for (x, y), t in self.splashes:  # little splashes
                s = 0.25 - (self.time - t)
                dd.draw_segment((x, y), (x - s, y + s), b2d.HexColor.LightSkyBlue)
                dd.draw_segment((x, y), (x + s, y + s), b2d.HexColor.LightSkyBlue)
            text = f"{int(self.pool.active.sum())} / {len(self.pool)} drops in the air, wind {self.wind:+.1f}"
        dd.draw_string((-11.5, 12.5), text, b2d.HexColor.White)
