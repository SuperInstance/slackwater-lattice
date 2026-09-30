"""
Line drawing and region operations on the Eisenstein lattice.

Provides hex-line drawing (analogous to Bresenham), flood-fill
region selection, and bounding-circle computation. All exact integer arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from slackwater_lattice.eisenstein import (
    EisensteinInteger,
    hex_distance,
    distance,
)


def hex_line(start: EisensteinInteger, goal: EisensteinInteger) -> list[EisensteinInteger]:
    """
    Draw a line on the hexagonal lattice from start to goal.

    Exact integer algorithm — no floating point, no drift:

      1. Convert (a, b) to cube coordinates (x, y, z) = (a, b - a, -b),
         which satisfy x + y + z = 0 and map the six neighbor steps
         ±(1,0), ±(0,1), ±(1,1) to unit cube steps.
      2. Interpolate along the segment with the exact rational lerp
         component i/d (integer numerators over the common denominator d
         = hex_distance(start, goal)).
      3. Round each component half-up (ties toward +∞) and re-derive the
         component with the largest rounding deviation so x + y + z = 0
         holds exactly. Deterministic tie-break: on equal deviations the
         z component is re-derived (the check order is x, then y, then z).

    Every point in the result is a valid EisensteinInteger, consecutive
    points are always neighbors (hex distance exactly 1), the endpoints
    are exact, and the line has exactly hex_distance(start, goal) + 1
    points. The result is identical on every platform (pure integer
    arithmetic).
    """
    if start == goal:
        return [start]

    d = hex_distance(start, goal)

    def cube(p: EisensteinInteger) -> tuple[int, int, int]:
        return (p.a, p.b - p.a, -p.b)

    ax, ay, az = cube(start)
    bx, by, bz = cube(goal)

    def round_half_up(num: int, den: int) -> int:
        """floor(num/den + 1/2) for den > 0 — ties round toward +∞."""
        return (2 * num + den) // (2 * den)

    result: list[EisensteinInteger] = []
    for i in range(d + 1):
        # Exact lerp numerators over the common denominator d.
        nx = (d - i) * ax + i * bx
        ny = (d - i) * ay + i * by
        nz = (d - i) * az + i * bz
        rx = round_half_up(nx, d)
        ry = round_half_up(ny, d)
        rz = round_half_up(nz, d)
        # Re-derive the component with the largest rounding deviation so
        # that x + y + z = 0 exactly (tie-break: z is re-derived last).
        dx = abs(rx * d - nx)
        dy = abs(ry * d - ny)
        dz = abs(rz * d - nz)
        if dx > dy and dx > dz:
            rx = -ry - rz
        elif dy > dz:
            ry = -rx - rz
        else:
            rz = -rx - ry
        result.append(EisensteinInteger(rx, -rz))

    return result


def flood_fill(
    start: EisensteinInteger,
    is_free: callable,
    max_radius: int = 100,
) -> set[EisensteinInteger]:
    """
    Flood fill from start, returning all connected free points.

    Args:
        start: The seed point.
        is_free: A function EisensteinInteger → bool. True if the point is passable.
        max_radius: Maximum hex distance to explore.

    Returns a set including start (if free) and all connected free points.
    """
    if not is_free(start):
        return set()

    visited: set[EisensteinInteger] = {start}
    frontier: list[EisensteinInteger] = [start]

    while frontier:
        current = frontier.pop(0)
        if hex_distance(start, current) >= max_radius:
            continue
        for neighbor in current.neighbors():
            if neighbor in visited:
                continue
            if is_free(neighbor):
                visited.add(neighbor)
                frontier.append(neighbor)

    return visited


def bounding_points(points: list[EisensteinInteger]) -> dict:
    """
    Compute bounding statistics for a set of lattice points.

    Returns dict with:
        min_a, max_a, min_b, max_b: coordinate bounds
        center: approximate center as EisensteinInteger
        diameter: max pairwise hex_distance
        count: number of points
    """
    if not points:
        return {"count": 0}

    a_vals = [p.a for p in points]
    b_vals = [p.b for p in points]

    center = EisensteinInteger(
        (min(a_vals) + max(a_vals)) // 2,
        (min(b_vals) + max(b_vals)) // 2,
    )

    # Compute diameter (lazy — fine for small sets)
    diameter = 0
    for i, p1 in enumerate(points):
        for p2 in points[i + 1:]:
            d = hex_distance(p1, p2)
            if d > diameter:
                diameter = d

    return {
        "min_a": min(a_vals),
        "max_a": max(a_vals),
        "min_b": min(b_vals),
        "max_b": max(b_vals),
        "center": center,
        "diameter": diameter,
        "count": len(points),
    }


def hex_ring(center: EisensteinInteger, radius: int) -> list[EisensteinInteger]:
    """
    Return the points at exactly `radius` hex distance from center.

    Unlike rings(), which returns all points within radius, this returns
    only the boundary — the points forming a hexagonal ring.

    For radius r, the ring has exactly 6r points (for r > 0).
    """
    if radius <= 0:
        return []

    result: list[EisensteinInteger] = []

    # Start at one corner of the ring and walk around
    # Using the six directions in order
    directions = [
        (1, 0),   # East
        (0, -1),  # Southwest
        (-1, 0),  # West
        (-1, -1), # Northwest... wait, let me use our actual directions
    ]

    # Actually, let's use the standard hex ring algorithm:
    # Start at center + radius * direction[0]
    # Then walk radius steps in direction[1], radius in direction[2], etc.

    from slackwater_lattice.eisenstein import NEIGHBOR_DIRECTIONS

    # Pick 6 directions that form a proper cycle around the hex
    # Our NEIGHBOR_DIRECTIONS: (1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1)
    # A proper ring-walk cycle: go in one direction, turn 60° each time
    cycle = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

    # Hmm, (-1, 1) and (1, -1) aren't in our NEIGHBOR_DIRECTIONS...
    # But they ARE valid hex directions in cube coords.
    # Let me just compute the ring directly.

    # Alternative: walk all points at distance r and filter
    for da in range(-radius, radius + 1):
        for db in range(-radius, radius + 1):
            if hex_distance(EisensteinInteger(0, 0), EisensteinInteger(da, db)) == radius:
                result.append(center + EisensteinInteger(da, db))

    result.sort()
    return result
