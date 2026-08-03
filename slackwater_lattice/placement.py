"""
Build placement on the Eisenstein lattice.

Every placed part snaps to a lattice point. The lattice guarantees:
  - Minimum spacing between parts
  - No floating-point misalignment
  - Isotropic neighborhoods (no privileged direction)
  - Exact collision detection (integer arithmetic)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

from slackwater_lattice.eisenstein import (
    EisensteinInteger,
    snap,
    distance,
    hex_distance,
)


@dataclass
class PlacementError(Exception):
    """Raised when a placement conflicts with an existing reservation."""
    point: EisensteinInteger
    existing: Optional[EisensteinInteger] = None

    def __str__(self) -> str:
        return f"Placement conflict at {self.point}: already occupied"


@dataclass
class BuildPlacement:
    """
    Manages occupied lattice points for a build.

    All positions are Eisenstein integers. Collision detection is
    exact integer comparison — O(1) hash lookup, no floating-point
    tolerance bands.

    Attributes:
        scale: Studs (or world units) per lattice unit. Default 4.0.
        occupied: Set of reserved lattice points.
        metadata: Optional per-point metadata (part type, agent, etc.)
    """

    scale: float = 4.0
    occupied: set[EisensteinInteger] = field(default_factory=set)
    metadata: dict[EisensteinInteger, dict] = field(default_factory=dict)

    # ── Snapping ─────────────────────────────────────────

    def snap_position(self, x: float, z: float) -> EisensteinInteger:
        """
        Snap a world-space (x, z) position to the nearest lattice point.

        The snap is the fundamental operation: continuous → discrete.
        After snapping, the position is exact and stable.
        """
        return snap(x, z, self.scale)

    def snap_rotation(self, rotation_deg: float) -> int:
        """
        Snap a rotation to the nearest 60° increment.

        The hexagonal lattice has 6-fold symmetry, so rotations
        quantize to {0, 60, 120, 180, 240, 300}.
        """
        return round(rotation_deg / 60.0) * 60

    # ── Collision detection ──────────────────────────────

    def check_collision(self, lattice_point: EisensteinInteger) -> bool:
        """
        Return True if the lattice point is already occupied.

        This is exact: two parts either occupy the same point or they don't.
        No tolerance bands. No floating-point fuzziness.
        """
        return lattice_point in self.occupied

    def check_region_clear(
        self,
        center: EisensteinInteger,
        radius: int = 1,
    ) -> bool:
        """
        Check that all lattice points within `radius` of center are free.
        """
        if self.check_collision(center):
            return False
        for neighbor in center.rings(radius):
            if neighbor in self.occupied:
                return False
        return True

    # ── Reservation ──────────────────────────────────────

    def reserve(
        self,
        lattice_point: EisensteinInteger,
        meta: Optional[dict] = None,
    ) -> EisensteinInteger:
        """
        Reserve a lattice point. Raises PlacementError if already occupied.

        Returns the lattice point (for chaining).
        """
        if lattice_point in self.occupied:
            raise PlacementError(point=lattice_point, existing=lattice_point)
        self.occupied.add(lattice_point)
        if meta:
            self.metadata[lattice_point] = meta
        return lattice_point

    def release(self, lattice_point: EisensteinInteger) -> bool:
        """
        Release a reserved lattice point. Returns True if it was occupied.
        """
        existed = lattice_point in self.occupied
        self.occupied.discard(lattice_point)
        self.metadata.pop(lattice_point, None)
        return existed

    def place(
        self,
        x: float,
        z: float,
        meta: Optional[dict] = None,
    ) -> EisensteinInteger:
        """
        Snap (x, z) to the lattice and reserve the point.
        Raises PlacementError on collision.
        """
        point = self.snap_position(x, z)
        return self.reserve(point, meta)

    # ── Queries ──────────────────────────────────────────

    def nearest_free(
        self,
        point: EisensteinInteger,
        max_radius: int = 20,
    ) -> Optional[EisensteinInteger]:
        """
        Find the nearest unoccupied lattice point to `point`,
        searching outward in rings. Returns None if all occupied
        within max_radius.
        """
        if not self.check_collision(point):
            return point
        for radius in range(1, max_radius + 1):
            for candidate in point.rings(radius):
                if not self.check_collision(candidate):
                    return candidate
        return None

    def occupied_neighbors(self, point: EisensteinInteger) -> list[EisensteinInteger]:
        """Return the occupied neighbors of a lattice point."""
        return [n for n in point.neighbors() if n in self.occupied]

    def free_neighbors(self, point: EisensteinInteger) -> list[EisensteinInteger]:
        """Return the unoccupied neighbors of a lattice point."""
        return [n for n in point.neighbors() if n not in self.occupied]

    def boundary_points(self) -> list[EisensteinInteger]:
        """
        Return occupied points that have at least one free neighbor.
        These are the "frontier" of the build.
        """
        return [p for p in self.occupied if self.free_neighbors(p)]

    # ── Iteration ────────────────────────────────────────

    def __contains__(self, point: EisensteinInteger) -> bool:
        return self.check_collision(point)

    def __len__(self) -> int:
        return len(self.occupied)

    def __iter__(self) -> Iterator[EisensteinInteger]:
        return iter(self.occupied)

    # ── Statistics ───────────────────────────────────────

    def footprint_area(self) -> int:
        """
        Number of occupied lattice points. Each point represents
        scale² · (√3/2) area in world units (hexagonal Voronoï cell).
        """
        return len(self.occupied)

    def diameter(self) -> int:
        """
        Maximum hex distance between any two occupied points.
        A measure of how spread out the build is.
        """
        if len(self.occupied) < 2:
            return 0
        points = list(self.occupied)
        max_d = 0
        for i, p1 in enumerate(points):
            for p2 in points[i + 1:]:
                d = hex_distance(p1, p2)
                if d > max_d:
                    max_d = d
        return max_d
