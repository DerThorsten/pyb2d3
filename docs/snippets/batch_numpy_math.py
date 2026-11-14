import numpy as np

import pyb2d3 as b2d

world = b2d.World(gravity=(0, 0))
rng = np.random.default_rng(42)
n = 1000
bodies = b2d.Bodies()
for x, y in rng.uniform(-20, 20, size=(n, 2)):
    body = world.create_dynamic_body(position=(x, y), linear_damping=0.2)
    body.create_shape(b2d.shape_def(density=1.0), b2d.circle(radius=0.25))
    bodies.append(body)

center = np.array([0.0, 0.0])
strength = 50.0


def radial_force_field():
    """Pull every body towards the center (softened 1/r) and swirl it around."""
    delta = center - bodies.position  # (n, 2)
    distance = np.linalg.norm(delta, axis=1, keepdims=True)  # (n, 1)
    direction = delta / np.maximum(distance, 1e-3)
    tangent = np.stack([-direction[:, 1], direction[:, 0]], axis=1)
    magnitude = strength * bodies.mass[:, None] / (distance + 1.0)
    bodies.apply_force_to_center(magnitude * (direction + 0.5 * tangent))


def kinetic_energy():
    """Translational plus rotational kinetic energy of all bodies."""
    v = bodies.linear_velocity
    w = bodies.angular_velocity
    return 0.5 * np.sum(bodies.mass * np.sum(v * v, axis=1)) + 0.5 * np.sum(bodies.rotational_inertia * w * w)


energies = []
for _ in range(60):
    radial_force_field()
    world.step(1 / 60, 4)
    energies.append(kinetic_energy())

print(f"kinetic energy after 1 s: {energies[-1]:.1f} J")
assert energies[-1] > energies[0] > 0

# the same numbers with a python loop, to check the vectorized version
loop_energy = sum(
    0.5 * b.mass * (b.linear_velocity.x**2 + b.linear_velocity.y**2) + 0.5 * b.rotational_inertia * b.angular_velocity**2
    for b in bodies
)
assert np.isclose(loop_energy, kinetic_energy(), rtol=1e-4)

# statistics are one-liners: mean distance to the center, the fastest body
print("mean radius:", np.linalg.norm(bodies.position - center, axis=1).mean())
print("fastest body:", bodies[np.argmax(bodies.speed)])
