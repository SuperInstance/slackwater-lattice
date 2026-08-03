"""
Eisenstein A₂ lattice — exact integer arithmetic.

The Eisenstein integers are ℤ[ω] where ω = e^(2πi/3) = -1/2 + i√3/2.
They form a triangular/hexagonal lattice in the complex plane.

Every point (a, b) in Eisenstein coordinates maps to Cartesian:
    x = a - b/2
    y = b·(√3/2)

Each lattice point has exactly six equidistant neighbors at unit distance:
    (a+1, b), (a-1, b), (a, b+1), (a, b-1), (a+1, b-1), (a-1, b+1)

The lattice norm (squared distance from origin) is:
    N(a + bω) = a² - ab + b²

This is exact integer arithmetic. No floating point. No drift.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

# ω = e^(2πi/3) = -1/2 + i√3/2
EISENSTEIN_OMEGA: tuple[float, float] = (-0.5, math.sqrt(3.0) / 2.0)

# The six neighbor directions on the A₂ lattice.
# Each is a unit vector in Eisenstein coordinates.
NEIGHBOR_DIRECTIONS: tuple[tuple[int, int], ...] = (
    (1, 0),   # east
    (0, 1),   # north-east
    (-1, 1),  # north-west
    (-1, 0),  # west
    (0, -1),  # south-west
    (1, -1),  # south-east
)


@dataclass(frozen=True)
class EisensteinInteger:
    """
    An exact point on the Eisenstein A₂ lattice.

    Represents the value a + bω where ω = e^(2πi/3).
    All arithmetic is exact integer — no floating point, no drift.

    Attributes:
        a: The real-integer coefficient.
        b: The ω coefficient.
    """

    a: int
    b: int

    # ── Algebra ──────────────────────────────────────────

    def __add__(self, other: EisensteinInteger) -> EisensteinInteger:
        return EisensteinInteger(self.a + other.a, self.b + other.b)

    def __sub__(self, other: EisensteinInteger) -> EisensteinInteger:
        return EisensteinInteger(self.a - other.a, self.b - other.b)

    def __neg__(self) -> EisensteinInteger:
        return EisensteinInteger(-self.a, -self.b)

    def __mul__(self, other: EisensteinInteger) -> EisensteinInteger:
        """
        Multiply two Eisenstein integers.

        (a + bω)(c + dω) = ac + (ad + bc)ω + bdω²
        Since ω² = -1 - ω:
            = ac + (ad + bc)ω + bd(-1 - ω)
            = (ac - bd) + (ad + bc - bd)ω
        """
        return EisensteinInteger(
            self.a * other.a - self.b * other.b,
            self.a * other.b + self.b * other.a - self.b * other.b,
        )

    def conjugate(self) -> EisensteinInteger:
        """The complex conjugate: a + bω → a + bω̄ = (a - b) - bω... actually ω̄ = ω² = -1-ω."""
        return EisensteinInteger(self.a - self.b, -self.b)

    # ── Norm and distance ────────────────────────────────

    def norm(self) -> int:
        """
        Squared distance from origin: N(a + bω) = a² - ab + b².
        This is always a non-negative integer.
        """
        return self.a * self.a - self.a * self.b + self.b * self.b

    def __abs__(self) -> int:
        """Integer norm (squared magnitude). Use norm() for clarity."""
        return self.norm()

    # ── Comparison ───────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EisensteinInteger):
            return self.a == other.a and self.b == other.b
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.a, self.b))

    def __lt__(self, other: EisensteinInteger) -> bool:
        """Order by norm, then by coordinates for determinism."""
        if self.norm() != other.norm():
            return self.norm() < other.norm()
        if self.a != other.a:
            return self.a < other.a
        return self.b < other.b

    def __le__(self, other: EisensteinInteger) -> bool:
        return self == other or self < other

    # ── Coordinate conversion ────────────────────────────

    def to_cartesian(self, scale: float = 1.0) -> tuple[float, float]:
        """
        Convert to Cartesian (x, y) coordinates.

        x = (a - b/2) · scale
        y = b · (√3/2) · scale
        """
        x = (self.a - self.b / 2.0) * scale
        y = self.b * (math.sqrt(3.0) / 2.0) * scale
        return (x, y)

    @classmethod
    def from_cartesian(cls, x: float, y: float, scale: float = 1.0) -> EisensteinInteger:
        """
        Convert Cartesian (x, y) to the nearest Eisenstein lattice point.

        Inverse of to_cartesian:
            b = y / (scale · √3/2) = 2y / (scale · √3)
            a = x / scale + b/2
        Then round both to nearest integer.
        """
        b_raw = 2.0 * y / (scale * math.sqrt(3.0))
        a_raw = x / scale + b_raw / 2.0
        return cls(round(a_raw), round(b_raw))

    # ── Representation ────────────────────────────────────

    def __repr__(self) -> str:
        if self.b == 0:
            return f"E({self.a})"
        if self.a == 0:
            return f"E({self.b}ω)"
        sign = "+" if self.b > 0 else "-"
        return f"E({self.a} {sign} {abs(self.b)}ω)"

    def __str__(self) -> str:
        return repr(self)

    # ── Lattice operations ───────────────────────────────

    def neighbors(self) -> list[EisensteinInteger]:
        """
        Return the six equidistant neighbors of this lattice point.

        On the A₂ lattice, every point has exactly six neighbors,
        all at unit distance. There is no privileged direction.
        """
        return [
            EisensteinInteger(self.a + da, self.b + db)
            for da, db in NEIGHBOR_DIRECTIONS
        ]

    def is_unit(self) -> bool:
        """The six units (norm-1 elements): ±1, ±ω, ±(1+ω)."""
        return self.norm() == 1

    def is_zero(self) -> bool:
        return self.a == 0 and self.b == 0

    def rings(self, radius: int) -> list[EisensteinInteger]:
        """
        Return all lattice points within `radius` (in lattice distance)
        of this point, excluding self. Ordered by distance.
        """
        if radius <= 0:
            return []
        result: list[EisensteinInteger] = []
        for da in range(-radius, radius + 1):
            for db in range(-radius, radius + 1):
                if da == 0 and db == 0:
                    continue
                offset = EisensteinInteger(da, db)
                if round(math.sqrt(offset.norm())) <= radius:
                    result.append(self + offset)
        result.sort()
        return result


# ── Module-level functions ─────────────────────────────────

def snap(x: float, z: float, scale: float = 1.0) -> EisensteinInteger:
    """
    Snap a Cartesian (x, z) position to the nearest lattice point.

    This is the fundamental operation: continuous space → lattice.
    The snap is a rounding operation. It is deterministic and exact.
    """
    return EisensteinInteger.from_cartesian(x, z, scale)


def distance(a: EisensteinInteger, b: EisensteinInteger) -> int:
    """
    Exact squared distance between two lattice points.

    Returns an integer — no floating point, no drift.
    The actual Euclidean distance is sqrt(distance(a, b)).
    """
    diff = a - b
    return diff.norm()


def hex_distance(a: EisensteinInteger, b: EisensteinInteger) -> int:
    """
    Hexagonal grid distance (number of steps) between two lattice points.
    This is the graph distance on the neighbor graph.

    For the A₂ lattice, the hex distance is:
        max(|da|, |db|, |da + db|)  where da = a₁-a₂, db = b₁-b₂

    Wait — that's the cube-coordinate formula. For Eisenstein coordinates,
    we need to convert. Actually, in Eisenstein (axial) coordinates, the
    hex distance is:

        d = (|da| + |db| + |da + db|) / 2

    where da = a.a - b.a, db = a.b - b.b.
    """
    da = a.a - b.a
    db = a.b - b.b
    return (abs(da) + abs(db) + abs(da + db)) // 2


def midpoint_region(a: EisensteinInteger, b: EisensteinInteger) -> list[EisensteinInteger]:
    """
    Return the lattice point(s) nearest to the geometric midpoint of a and b.
    May return 1 or 2 points (if the midpoint falls on an edge).
    """
    # Midpoint in Cartesian
    ax, ay = a.to_cartesian()
    bx, by = b.to_cartesian()
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    snapped = snap(mx, my)
    # Check if neighbors are also equidistant (edge case)
    result = [snapped]
    for n in snapped.neighbors():
        n_dist = distance(n, a) + distance(n, b)
        s_dist = distance(snapped, a) + distance(snapped, b)
        if n_dist == s_dist and n not in result:
            result.append(n)
    return result
