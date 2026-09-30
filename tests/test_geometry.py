"""Tests for geometry module: hex_line, flood_fill, bounding_points, hex_ring."""

import pytest
from slackwater_lattice.eisenstein import EisensteinInteger, hex_distance
from slackwater_lattice.geometry import (
    hex_line,
    flood_fill,
    bounding_points,
    hex_ring,
)


# ── hex_line tests ────────────────────────────────────────────────

class TestHexLine:
    def test_same_point(self):
        p = EisensteinInteger(3, 4)
        result = hex_line(p, p)
        assert result == [p]

    def test_adjacent_points(self):
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(1, 0)
        result = hex_line(a, b)
        assert result == [a, b]

    def test_horizontal_line(self):
        """A line along the a-axis."""
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(5, 0)
        result = hex_line(a, b)
        assert result[0] == a
        assert result[-1] == b
        # Every consecutive pair should be neighbors or the same
        for i in range(len(result) - 1):
            d = hex_distance(result[i], result[i + 1])
            assert d <= 1, f"Gap at {i}: {result[i]} → {result[i+1]}, d={d}"

    def test_diagonal_line(self):
        """A line along the b-axis."""
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(0, 5)
        result = hex_line(a, b)
        assert result[0] == a
        assert result[-1] == b
        for i in range(len(result) - 1):
            d = hex_distance(result[i], result[i + 1])
            assert d <= 1

    def test_line_length_matches_distance(self):
        """The line should have roughly hex_distance + 1 points."""
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(3, 4)
        result = hex_line(a, b)
        expected = hex_distance(a, b) + 1
        # Allow some slack due to snapping
        assert abs(len(result) - expected) <= 2

    def test_negative_coordinates(self):
        a = EisensteinInteger(-3, -2)
        b = EisensteinInteger(2, 3)
        result = hex_line(a, b)
        assert result[0] == a
        assert result[-1] == b

    def test_consecutive_points_are_neighbors(self):
        """Every step in the line should be to a neighbor (or same point)."""
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(4, -3)
        result = hex_line(a, b)
        for i in range(len(result) - 1):
            d = hex_distance(result[i], result[i + 1])
            assert d <= 1, f"Non-adjacent step at {i}: {result[i]} → {result[i+1]}"


# ── hex_line exactness tests (task 67-a) ──────────────────────────
#
# v0.1.0 interpolated the line in Cartesian floats and snapped each sample
# with Python's banker's rounding. For segments whose midpoint falls on a
# hexagon edge (offsets like (1,-1), i.e. the 1-ω diagonal), the mid sample
# tied between two lattice points and could snap back onto an endpoint —
# the middle point was dropped and consecutive line points ended up at hex
# distance 2. Brute force on v0.1.0 over the ±12 box: 60,376 of 390,000
# ordered pairs produced a non-neighbor gap. These tests pin the contract:
# exact endpoints, exact length, and every consecutive pair hex-neighbors.


class TestHexLineExact:
    # Deterministic failing pairs found by the v0.1.0 brute-force audit
    # (smallest witnesses, sorted by hex distance).
    RED_CASES = [
        (EisensteinInteger(0, 0), EisensteinInteger(1, -1)),   # d=2: middle dropped
        (EisensteinInteger(1, 1), EisensteinInteger(2, 0)),    # d=2
        (EisensteinInteger(-2, 0), EisensteinInteger(-3, 1)),  # d=2
        (EisensteinInteger(-3, 2), EisensteinInteger(0, 1)),   # d=4: one gap
        (EisensteinInteger(-3, 3), EisensteinInteger(0, 0)),   # d=6: two gaps
    ]

    @pytest.mark.parametrize("start,goal", RED_CASES)
    def test_consecutive_points_are_hex_neighbors(self, start, goal):
        line = hex_line(start, goal)
        assert line[0] == start
        assert line[-1] == goal
        for i in range(len(line) - 1):
            d = hex_distance(line[i], line[i + 1])
            assert d == 1, (
                f"{start}→{goal}: step {i} {line[i]} → {line[i + 1]} at hex distance {d}, not 1"
            )

    @pytest.mark.parametrize("start,goal", RED_CASES)
    def test_line_length_is_distance_plus_one(self, start, goal):
        line = hex_line(start, goal)
        expected = hex_distance(start, goal) + 1
        assert len(line) == expected, (
            f"{start}→{goal}: line has {len(line)} points, expected {expected}"
        )

    def test_tie_break_deterministic(self):
        """Documented tie-break: half-integer lerp components round half-up
        (toward +∞); on a hexagon-edge tie the deviation correction re-derives
        the cube z component. E(0,0)→E(1,-1) therefore goes through E(1,0)."""
        line = hex_line(EisensteinInteger(0, 0), EisensteinInteger(1, -1))
        assert line == [
            EisensteinInteger(0, 0),
            EisensteinInteger(1, 0),
            EisensteinInteger(1, -1),
        ]

    def test_all_pairs_small_box_are_valid_lines(self):
        """Every ordered pair in the ±3 box: exact endpoints, exact length,
        consecutive points at hex distance exactly 1."""
        pts = [EisensteinInteger(a, b) for a in range(-3, 4) for b in range(-3, 4)]
        for s in pts:
            for g in pts:
                if s == g:
                    continue
                line = hex_line(s, g)
                d = hex_distance(s, g)
                assert line[0] == s and line[-1] == g
                assert len(line) == d + 1, f"{s}→{g}: length {len(line)} != {d + 1}"
                for i in range(len(line) - 1):
                    step = hex_distance(line[i], line[i + 1])
                    assert step == 1, f"{s}→{g}: gap of {step} at index {i}"


# ── flood_fill tests ──────────────────────────────────────────────

class TestFloodFill:
    def test_single_point(self):
        """With a one-point free region."""
        result = flood_fill(EisensteinInteger(0, 0), lambda p: p == EisensteinInteger(0, 0))
        assert result == {EisensteinInteger(0, 0)}

    def test_all_free(self):
        """Everything is free — should fill up to max_radius."""
        result = flood_fill(EisensteinInteger(0, 0), lambda p: True, max_radius=2)
        # Should include all points within distance 2 of origin
        assert EisensteinInteger(0, 0) in result
        assert EisensteinInteger(1, 0) in result
        assert EisensteinInteger(2, 0) in result
        # Should NOT include points at distance 3
        assert EisensteinInteger(3, 0) not in result

    def test_blocked_start(self):
        """If the start is blocked, return empty set."""
        result = flood_fill(EisensteinInteger(0, 0), lambda p: False)
        assert result == set()

    def test_wall_blocks_expansion(self):
        """A wall of blocked points should contain the fill."""
        blocked = {EisensteinInteger(1, 0), EisensteinInteger(0, 1),
                   EisensteinInteger(1, 1), EisensteinInteger(-1, 0),
                   EisensteinInteger(0, -1), EisensteinInteger(-1, -1)}
        result = flood_fill(EisensteinInteger(0, 0), lambda p: p not in blocked, max_radius=10)
        assert result == {EisensteinInteger(0, 0)}

    def test_corridor(self):
        """Free corridor along a-axis."""
        free_points = {EisensteinInteger(a, 0) for a in range(5)}
        result = flood_fill(EisensteinInteger(0, 0), lambda p: p in free_points, max_radius=20)
        assert result == free_points

    def test_max_radius_limits_spread(self):
        """max_radius should limit how far the fill spreads."""
        for r in [1, 2, 3]:
            result = flood_fill(EisensteinInteger(0, 0), lambda p: True, max_radius=r)
            # Every point should be within distance r
            for p in result:
                assert hex_distance(EisensteinInteger(0, 0), p) <= r


# ── bounding_points tests ─────────────────────────────────────────

class TestBoundingPoints:
    def test_empty(self):
        result = bounding_points([])
        assert result["count"] == 0

    def test_single_point(self):
        p = EisensteinInteger(3, 4)
        result = bounding_points([p])
        assert result["count"] == 1
        assert result["min_a"] == 3
        assert result["max_a"] == 3
        assert result["diameter"] == 0

    def test_two_points(self):
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(3, 4)
        result = bounding_points([a, b])
        assert result["min_a"] == 0
        assert result["max_a"] == 3
        assert result["diameter"] == hex_distance(a, b)

    def test_center(self):
        points = [EisensteinInteger(0, 0), EisensteinInteger(4, 4)]
        result = bounding_points(points)
        assert result["center"] == EisensteinInteger(2, 2)

    def test_negative_coords(self):
        points = [EisensteinInteger(-3, -2), EisensteinInteger(1, 5)]
        result = bounding_points(points)
        assert result["min_a"] == -3
        assert result["max_a"] == 1
        assert result["min_b"] == -2
        assert result["max_b"] == 5

    def test_many_points(self):
        points = [EisensteinInteger(a, 0) for a in range(10)]
        result = bounding_points(points)
        assert result["count"] == 10
        assert result["min_a"] == 0
        assert result["max_a"] == 9
        assert result["diameter"] == 9


# ── hex_ring tests ────────────────────────────────────────────────

class TestHexRing:
    def test_radius_zero(self):
        """Ring at radius 0 is empty."""
        result = hex_ring(EisensteinInteger(0, 0), 0)
        assert result == []

    def test_radius_one_has_six(self):
        """Ring at radius 1 should have exactly 6 points (the neighbors)."""
        result = hex_ring(EisensteinInteger(0, 0), 1)
        assert len(result) == 6

    def test_radius_two_count(self):
        """Ring at radius 2 should have 12 points (6*2)."""
        result = hex_ring(EisensteinInteger(0, 0), 2)
        assert len(result) == 12

    def test_all_points_at_correct_distance(self):
        """Every point in ring r should be at hex_distance r from center."""
        center = EisensteinInteger(3, 2)
        for r in [1, 2, 3]:
            result = hex_ring(center, r)
            for p in result:
                assert hex_distance(center, p) == r, f"{p} at distance {hex_distance(center, p)}, expected {r}"

    def test_offset_center(self):
        """Ring around a non-origin center."""
        center = EisensteinInteger(5, 5)
        result = hex_ring(center, 1)
        assert len(result) == 6
        for p in result:
            assert hex_distance(center, p) == 1

    def test_no_overlap_between_rings(self):
        """Rings at different radii should not share points."""
        r1 = set(hex_ring(EisensteinInteger(0, 0), 1))
        r2 = set(hex_ring(EisensteinInteger(0, 0), 2))
        assert r1.isdisjoint(r2)
