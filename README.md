# slackwater-lattice

![tests](https://img.shields.io/badge/tests-52%20passed-brightgreen)
![version](https://img.shields.io/badge/version-0.1.0-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)

Exact integer geometry on the Eisenstein A₂ hexagonal lattice — the densest packing of circles in a plane. Every point has exactly six equidistant neighbors. No privileged axis. No floating-point drift. This package provides Eisenstein integer arithmetic, build placement with collision detection, and A* pathfinding on the hexagonal neighbor graph.

## Installation

```bash
pip install slackwater-lattice
```

## Mathematical Foundation

Eisenstein integers are ℤ[ω] where ω = e^(2πi/3) = −1/2 + i√3/2. They form a triangular/hexagonal lattice in the complex plane.

**Coordinate system:** A point (a, b) in Eisenstein coordinates maps to Cartesian:
```
x = (a − b/2) · scale
y = b · (√3/2) · scale
```

**Norm (squared distance from origin):**
```
N(a + bω) = a² − ab + b²
```

This is always a non-negative integer. All arithmetic is exact — no floating point, no drift.

**Six neighbor directions (unit norm elements):**

| Direction | Offset | Cartesian |
|---|---|---|
| +1 | (1, 0) | East |
| −1 | (−1, 0) | West |
| +ω | (0, 1) | Northeast |
| −ω | (0, −1) | Southwest |
| +(1+ω) | (1, 1) | Southeast |
| −(1+ω) | (−1, −1) | Northwest |

## API Reference

### EisensteinInteger

```python
from slackwater_lattice import EisensteinInteger

EisensteinInteger(a: int, b: int)
```

An exact point on the A₂ lattice. Represents the value `a + bω`. Frozen dataclass — hashable, comparable.

**Arithmetic operators:**

| Operator | Signature | Formula |
|---|---|---|
| `+` | `(ei) -> ei` | `(a+c, b+d)` |
| `−` | `(ei) -> ei` | `(a−c, b−d)` |
| `*` | `(ei) -> ei` | `(ac−bd, ad+bc−bd)` |
| `conjugate()` | `() -> ei` | `(a−b, −b)` |
| `norm()` | `() -> int` | `a² − ab + b²` |
| `−` (unary) | `() -> ei` | `(−a, −b)` |

**Coordinate conversion:**

```python
ei.to_cartesian(scale: float = 1.0) -> tuple[float, float]
EisensteinInteger.from_cartesian(x: float, y: float, scale: float = 1.0) -> EisensteinInteger
```

The `from_cartesian` method rounds to the nearest lattice point. This is the **snapping algorithm** — continuous space → discrete lattice. It is deterministic and exact.

**Lattice operations:**

```python
ei.neighbors() -> list[EisensteinInteger]           # 6 equidistant neighbors
ei.rings(radius: int) -> list[EisensteinInteger]     # all points within hex distance
ei.is_unit() -> bool                                  # norm == 1?
ei.is_zero() -> bool                                  # a==0 and b==0?
```

**Module-level functions:**

```python
snap(x: float, z: float, scale: float = 1.0) -> EisensteinInteger
distance(a: EisensteinInteger, b: EisensteinInteger) -> int        # squared Euclidean
hex_distance(a: EisensteinInteger, b: EisensteinInteger) -> int    # graph steps
midpoint_region(a: EisensteinInteger, b: EisensteinInteger) -> list[EisensteinInteger]
```

**Hex distance formula:**

```
if da·db ≥ 0:  d = max(|da|, |db|)     # same sector
else:          d = |da| + |db|          # opposite sectors
```

### BuildPlacement

```python
from slackwater_lattice import BuildPlacement, PlacementError

BuildPlacement(
    scale: float = 4.0,    # world units per lattice unit
)
```

Manages occupied lattice points for a build. Collision detection is exact integer comparison — O(1) hash lookup, no tolerance bands.

**Snapping:**

```python
bp.snap_position(x: float, z: float) -> EisensteinInteger
bp.snap_rotation(rotation_deg: float) -> int    # nearest 60° increment
```

**Collision and reservation:**

```python
bp.check_collision(lattice_point: EisensteinInteger) -> bool
bp.check_region_clear(center: EisensteinInteger, radius: int = 1) -> bool
bp.reserve(lattice_point: EisensteinInteger, meta: dict | None = None) -> EisensteinInteger
bp.release(lattice_point: EisensteinInteger) -> bool
bp.place(x: float, z: float, meta: dict | None = None) -> EisensteinInteger  # snap + reserve
```

`reserve()` raises `PlacementError` on collision. `place()` is the combined snap-and-reserve convenience.

**Queries:**

```python
bp.nearest_free(point: EisensteinInteger, max_radius: int = 20) -> EisensteinInteger | None
bp.occupied_neighbors(point: EisensteinInteger) -> list[EisensteinInteger]
bp.free_neighbors(point: EisensteinInteger) -> list[EisensteinInteger]
bp.boundary_points() -> list[EisensteinInteger]    # frontier of the build
bp.footprint_area() -> int                          # count of occupied points
bp.diameter() -> int                                # max hex distance between any two points
```

Supports `in` operator, `len()`, and iteration.

### LatticePathfinder

```python
from slackwater_lattice import LatticePathfinder, LatticePath

LatticePathfinder(
    placement: BuildPlacement,
    allow_through_occupied: bool = False,
)
```

A* pathfinder on the Eisenstein lattice. Uses `hex_distance` as the heuristic — admissible and consistent on the neighbor graph, guaranteeing optimal paths.

**Methods:**

```python
pf.find_path(
    start: EisensteinInteger,
    goal: EisensteinInteger,
    max_steps: int = 10_000,
) -> LatticePath | None
```

Returns the shortest path through free lattice points, or `None` if unreachable.

```python
pf.find_all_paths(start, goal, max_paths: int = 5) -> list[LatticePath]
pf.reachable(start, max_distance: int = 20) -> dict[EisensteinInteger, int]
```

`find_all_paths` uses a simplified Yen's algorithm for k-shortest paths. `reachable` does BFS within `max_distance` steps.

**LatticePath:**

```python
@dataclass
class LatticePath:
    points: list[EisensteinInteger]
    
    length() -> int      # number of steps (edges)
    is_empty() -> bool   # single point or less
```

Supports iteration and indexing.

## Examples

### Basic lattice arithmetic

```python
from slackwater_lattice import EisensteinInteger, distance, hex_distance

z = EisensteinInteger(3, 1)
print(z.norm())            # 7  (9 - 3 + 1)
print(z.to_cartesian(4.0)) # (10.0, 3.464...)

neighbors = z.neighbors()  # 6 points at distance 1
```

### Snapping world positions to the lattice

```python
from slackwater_lattice import BuildPlacement

bp = BuildPlacement(scale=4.0)
point = bp.place(10.5, 3.2)
print(point)  # nearest lattice point to (10.5, 3.2) at scale 4

# Collision-free placement
free = bp.nearest_free(point)
```

### Pathfinding around obstacles

```python
from slackwater_lattice import EisensteinInteger, BuildPlacement, LatticePathfinder

bp = BuildPlacement()
# Build a wall
for i in range(-2, 3):
    bp.reserve(EisensteinInteger(0, i))

pf = LatticePathfinder(placement=bp)
path = pf.find_path(EisensteinInteger(-3, 0), EisensteinInteger(3, 0))
print(path)         # LatticePath(E(-3) → E(-2) → ... → E(3))
print(path.length()) # hex-optimal, avoids all wall points
```

## License

MIT
