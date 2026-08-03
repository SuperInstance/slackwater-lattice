"""
Tests for slackwater-lattice.

Exercises the Eisenstein integer arithmetic, build placement,
and pathfinding on the hexagonal lattice.
"""

import math
import pytest

from slackwater_lattice import EisensteinInteger, BuildPlacement, LatticePathfinder
from slackwater_lattice.eisenstein import (
    snap,
    distance,
    hex_distance,
    EISENSTEIN_OMEGA,
    NEIGHBOR_DIRECTIONS,
)
from slackwater_lattice.placement import PlacementError
from slackwater_lattice.pathfinding import LatticePath


class TestEisensteinInteger:
    """Test exact integer arithmetic on the A₂ lattice."""

    def test_origin(self):
        z = EisensteinInteger(0, 0)
        assert z.norm() == 0
        assert z.is_zero()
        assert not z.is_unit()

    def test_units(self):
        """The six units have norm 1."""
        units = [
            EisensteinInteger(1, 0),
            EisensteinInteger(-1, 0),
            EisensteinInteger(0, 1),
            EisensteinInteger(0, -1),
            EisensteinInteger(1, 1),
            EisensteinInteger(-1, -1),
        ]
        for u in units:
            assert u.norm() == 1, f"{u} should be a unit"
            assert u.is_unit()

    def test_addition(self):
        z1 = EisensteinInteger(3, 1)
        z2 = EisensteinInteger(1, 2)
        assert z1 + z2 == EisensteinInteger(4, 3)

    def test_subtraction(self):
        z1 = EisensteinInteger(5, 3)
        z2 = EisensteinInteger(2, 1)
        assert z1 - z2 == EisensteinInteger(3, 2)

    def test_negation(self):
        z = EisensteinInteger(3, -2)
        assert -z == EisensteinInteger(-3, 2)

    def test_multiplication(self):
        """(a + bω)(c + dω) = (ac - bd) + (ad + bc - bd)ω"""
        z1 = EisensteinInteger(2, 1)
        z2 = EisensteinInteger(3, 2)
        # (2+ω)(3+2ω) = 6 + 4ω + 3ω + 2ω² = 6 + 7ω + 2(-1-ω) = 4 + 5ω
        result = z1 * z2
        assert result == EisensteinInteger(4, 5)

    def test_multiplication_identity(self):
        z = EisensteinInteger(7, 3)
        one = EisensteinInteger(1, 0)
        assert z * one == z

    def test_norm_always_nonneg(self):
        """N(a + bω) = a² - ab + b² ≥ 0 for all integers a, b."""
        for a in range(-10, 11):
            for b in range(-10, 11):
                z = EisensteinInteger(a, b)
                assert z.norm() >= 0, f"Norm of {z} is negative"

    def test_norm_known_values(self):
        assert EisensteinInteger(1, 0).norm() == 1
        assert EisensteinInteger(1, 1).norm() == 1  # 1 - 1 + 1
        assert EisensteinInteger(2, 0).norm() == 4
        assert EisensteinInteger(2, 1).norm() == 3  # 4 - 2 + 1
        assert EisensteinInteger(3, 1).norm() == 7  # 9 - 3 + 1

    def test_neighbors_count(self):
        """Every point has exactly 6 neighbors."""
        z = EisensteinInteger(5, 3)
        nbrs = z.neighbors()
        assert len(nbrs) == 6

    def test_neighbors_at_unit_distance(self):
        """All neighbors are at distance 1."""
        z = EisensteinInteger(7, 2)
        for n in z.neighbors():
            assert distance(z, n) == 1

    def test_neighbors_distinct(self):
        z = EisensteinInteger(0, 0)
        nbrs = z.neighbors()
        assert len(set(nbrs)) == 6

    def test_cartesian_roundtrip(self):
        """to_cartesian → from_cartesian should be identity for lattice points."""
        for a in range(-5, 6):
            for b in range(-5, 6):
                z = EisensteinInteger(a, b)
                x, y = z.to_cartesian(scale=4.0)
                recovered = EisensteinInteger.from_cartesian(x, y, scale=4.0)
                assert z == recovered, f"Roundtrip failed for {z}: got {recovered}"

    def test_snap_origin(self):
        """Snapping (0, 0) should give origin."""
        assert snap(0.0, 0.0) == EisensteinInteger(0, 0)

    def test_snap_near_origin(self):
        """Points very close to origin snap to origin."""
        for x in [-0.2, -0.1, 0.0, 0.1, 0.2]:
            for z in [-0.2, -0.1, 0.0, 0.1, 0.2]:
                if math.sqrt(x * x + z * z) < 0.3:
                    assert snap(x, z) == EisensteinInteger(0, 0), f"({x}, {z}) should snap to origin"

    def test_distance_symmetric(self):
        a = EisensteinInteger(3, 7)
        b = EisensteinInteger(10, 2)
        assert distance(a, b) == distance(b, a)

    def test_distance_to_self(self):
        z = EisensteinInteger(42, 17)
        assert distance(z, z) == 0

    def test_hex_distance_to_self(self):
        z = EisensteinInteger(5, 5)
        assert hex_distance(z, z) == 0

    def test_hex_distance_neighbor(self):
        z = EisensteinInteger(0, 0)
        for n in z.neighbors():
            assert hex_distance(z, n) == 1

    def test_hex_distance_known(self):
        """Hex distance from origin."""
        assert hex_distance(EisensteinInteger(0, 0), EisensteinInteger(3, 0)) == 3
        assert hex_distance(EisensteinInteger(0, 0), EisensteinInteger(0, 3)) == 3
        assert hex_distance(EisensteinInteger(0, 0), EisensteinInteger(3, 3)) == 6
        assert hex_distance(EisensteinInteger(0, 0), EisensteinInteger(1, 1)) == 1
        assert hex_distance(EisensteinInteger(0, 0), EisensteinInteger(2, -1)) == 2

    def test_equality(self):
        assert EisensteinInteger(3, 1) == EisensteinInteger(3, 1)
        assert EisensteinInteger(3, 1) != EisensteinInteger(3, 2)
        assert EisensteinInteger(3, 1) != 3  # type mismatch

    def test_hashable(self):
        """EisensteinInteger is hashable (frozen dataclass)."""
        s = {EisensteinInteger(1, 0), EisensteinInteger(1, 0), EisensteinInteger(0, 1)}
        assert len(s) == 2

    def test_rings(self):
        """Rings(radius=1) should return the 6 neighbors at hex distance 1."""
        z = EisensteinInteger(0, 0)
        r1 = z.rings(1)
        assert len(r1) == 6
        for p in r1:
            assert hex_distance(z, p) == 1

    def test_repr(self):
        assert "E(3)" in repr(EisensteinInteger(3, 0))
        assert "ω" in repr(EisensteinInteger(0, 1))


class TestBuildPlacement:
    """Test lattice-based build placement."""

    def test_reserve_and_check(self):
        bp = BuildPlacement(scale=4.0)
        p = EisensteinInteger(3, 1)
        assert not bp.check_collision(p)
        bp.reserve(p)
        assert bp.check_collision(p)

    def test_double_reserve_raises(self):
        bp = BuildPlacement()
        p = EisensteinInteger(2, 2)
        bp.reserve(p)
        with pytest.raises(PlacementError):
            bp.reserve(p)

    def test_release(self):
        bp = BuildPlacement()
        p = EisensteinInteger(1, 1)
        bp.reserve(p)
        assert bp.check_collision(p)
        assert bp.release(p)
        assert not bp.check_collision(p)

    def test_place_from_cartesian(self):
        bp = BuildPlacement(scale=4.0)
        point = bp.place(4.0, 0.0)  # Should snap to (1, 0) at scale 4
        assert isinstance(point, EisensteinInteger)
        assert bp.check_collision(point)

    def test_snap_rotation(self):
        bp = BuildPlacement()
        assert bp.snap_rotation(0) == 0
        assert bp.snap_rotation(55) == 60
        assert bp.snap_rotation(45) == 60
        assert bp.snap_rotation(29) == 0
        assert bp.snap_rotation(180) == 180
        assert bp.snap_rotation(315) == 300
        assert bp.snap_rotation(30) == 0  # 30 rounds down to 0

    def test_containment(self):
        bp = BuildPlacement()
        p = EisensteinInteger(5, 5)
        bp.reserve(p)
        assert p in bp
        assert EisensteinInteger(0, 0) not in bp

    def test_nearest_free_immediate(self):
        bp = BuildPlacement()
        p = EisensteinInteger(3, 3)
        assert bp.nearest_free(p) == p

    def test_nearest_free_with_occupancy(self):
        bp = BuildPlacement()
        origin = EisensteinInteger(0, 0)
        bp.reserve(origin)
        nearest = bp.nearest_free(origin)
        assert nearest is not None
        assert nearest != origin
        # Should be a direct neighbor at hex distance 1
        assert hex_distance(origin, nearest) == 1

    def test_free_neighbors(self):
        bp = BuildPlacement()
        p = EisensteinInteger(2, 2)
        bp.reserve(p)
        nbrs = bp.free_neighbors(p)
        assert len(nbrs) == 6  # All neighbors free since only p is occupied

    def test_occupied_neighbors(self):
        bp = BuildPlacement()
        center = EisensteinInteger(0, 0)
        n1 = EisensteinInteger(1, 0)
        bp.reserve(center)
        bp.reserve(n1)
        result = bp.occupied_neighbors(center)
        assert n1 in result

    def test_boundary_points(self):
        bp = BuildPlacement()
        p1 = EisensteinInteger(0, 0)
        p2 = EisensteinInteger(1, 0)
        bp.reserve(p1)
        bp.reserve(p2)
        boundary = bp.boundary_points()
        assert p1 in boundary
        assert p2 in boundary

    def test_metadata(self):
        bp = BuildPlacement()
        p = EisensteinInteger(1, 1)
        bp.reserve(p, {"type": "wall", "agent": "lucineer"})
        assert bp.metadata[p]["type"] == "wall"
        assert bp.metadata[p]["agent"] == "lucineer"

    def test_len_and_iter(self):
        bp = BuildPlacement()
        bp.reserve(EisensteinInteger(0, 0))
        bp.reserve(EisensteinInteger(1, 0))
        bp.reserve(EisensteinInteger(0, 1))
        assert len(bp) == 3
        assert EisensteinInteger(0, 0) in list(bp)

    def test_diameter(self):
        bp = BuildPlacement()
        bp.reserve(EisensteinInteger(0, 0))
        bp.reserve(EisensteinInteger(5, 0))
        d = bp.diameter()
        assert d == 5

    def test_diameter_single(self):
        bp = BuildPlacement()
        bp.reserve(EisensteinInteger(3, 3))
        assert bp.diameter() == 0


class TestPathfinding:
    """Test A* pathfinding on the lattice."""

    def test_direct_path(self):
        bp = BuildPlacement()
        pf = LatticePathfinder(placement=bp)
        start = EisensteinInteger(0, 0)
        goal = EisensteinInteger(3, 0)
        path = pf.find_path(start, goal)
        assert path is not None
        assert path.points[0] == start
        assert path.points[-1] == goal
        assert path.length() == 3

    def test_path_to_self(self):
        bp = BuildPlacement()
        pf = LatticePathfinder(placement=bp)
        z = EisensteinInteger(2, 2)
        path = pf.find_path(z, z)
        assert path is not None
        assert len(path.points) == 1
        assert path.is_empty()

    def test_path_around_obstacle(self):
        bp = BuildPlacement()
        # Create a wall
        for i in range(-2, 3):
            bp.reserve(EisensteinInteger(0, i))
        pf = LatticePathfinder(placement=bp)
        start = EisensteinInteger(-3, 0)
        goal = EisensteinInteger(3, 0)
        path = pf.find_path(start, goal)
        assert path is not None
        assert path.points[0] == start
        assert path.points[-1] == goal
        # Path should avoid all occupied points
        for p in path.points[1:-1]:
            assert not bp.check_collision(p), f"Path goes through occupied {p}"

    def test_no_path_when_blocked(self):
        bp = BuildPlacement()
        # Surround goal completely
        goal = EisensteinInteger(5, 5)
        bp.reserve(goal)
        for n in goal.neighbors():
            bp.reserve(n)
        pf = LatticePathfinder(placement=bp)
        path = pf.find_path(EisensteinInteger(0, 0), goal)
        assert path is None

    def test_path_length_optimal(self):
        bp = BuildPlacement()
        pf = LatticePathfinder(placement=bp)
        start = EisensteinInteger(0, 0)
        goal = EisensteinInteger(4, 2)
        path = pf.find_path(start, goal)
        assert path is not None
        expected_len = hex_distance(start, goal)
        assert path.length() == expected_len

    def test_reachable(self):
        bp = BuildPlacement()
        bp.reserve(EisensteinInteger(0, 0))
        pf = LatticePathfinder(placement=bp)
        reachable = pf.reachable(EisensteinInteger(2, 0), max_distance=3)
        # Should have several reachable points
        assert len(reachable) > 0
        # Start point excluded
        assert EisensteinInteger(2, 0) not in reachable
        # A point at distance 1 should be there
        assert EisensteinInteger(3, 0) in reachable
        assert reachable[EisensteinInteger(3, 0)] == 1

    def test_path_with_allow_through(self):
        bp = BuildPlacement()
        # Block the direct path
        bp.reserve(EisensteinInteger(1, 0))
        bp.reserve(EisensteinInteger(2, 0))
        pf = LatticePathfinder(placement=bp, allow_through_occupied=True)
        # With allow_through, should still find a path
        path = pf.find_path(EisensteinInteger(0, 0), EisensteinInteger(3, 0))
        assert path is not None


class TestLatticePath:
    """Test the LatticePath dataclass."""

    def test_length(self):
        p = LatticePath([
            EisensteinInteger(0, 0),
            EisensteinInteger(1, 0),
            EisensteinInteger(2, 0),
        ])
        assert p.length() == 2

    def test_empty_path(self):
        p = LatticePath([EisensteinInteger(0, 0)])
        assert p.is_empty()
        assert p.length() == 0

    def test_iteration(self):
        pts = [EisensteinInteger(0, 0), EisensteinInteger(1, 0)]
        p = LatticePath(pts)
        for original, from_path in zip(pts, p):
            assert original == from_path


class TestSixNeighborDirections:
    """Verify the six directions are correct and complete."""

    def test_six_directions(self):
        assert len(NEIGHBOR_DIRECTIONS) == 6

    def test_directions_distinct(self):
        assert len(set(NEIGHBOR_DIRECTIONS)) == 6

    def test_all_unit_norm(self):
        """Each direction should have norm 1."""
        for a, b in NEIGHBOR_DIRECTIONS:
            assert EisensteinInteger(a, b).norm() == 1
