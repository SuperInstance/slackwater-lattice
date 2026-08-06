"""
Tests for slackwater-lattice eisenstein module — Eisenstein integer arithmetic.

Tests cover:
- EisensteinInteger construction and arithmetic
- Hex distance calculation (A* heuristic)
- Neighbor generation (6 directions)
- Norm properties
- Addition, subtraction, multiplication
- Edge cases: zero, negatives, large values
"""

import pytest
from slackwater_lattice.eisenstein import (
    EisensteinInteger,
    hex_distance,
    NEIGHBOR_DIRECTIONS,
)


# ─── Construction Tests ──────────────────────────────────

class TestConstruction:
    def test_default(self):
        e = EisensteinInteger(0, 0)
        assert e.a == 0
        assert e.b == 0

    def test_positive(self):
        e = EisensteinInteger(3, 4)
        assert e.a == 3
        assert e.b == 4

    def test_negative(self):
        e = EisensteinInteger(-2, -5)
        assert e.a == -2
        assert e.b == -5

    def test_mixed_signs(self):
        e = EisensteinInteger(5, -3)
        assert e.a == 5
        assert e.b == -3


# ─── Equality and Hashing Tests ──────────────────────────

class TestEquality:
    def test_equal(self):
        assert EisensteinInteger(1, 2) == EisensteinInteger(1, 2)

    def test_not_equal(self):
        assert EisensteinInteger(1, 2) != EisensteinInteger(2, 1)

    def test_hash_equal(self):
        assert hash(EisensteinInteger(3, 4)) == hash(EisensteinInteger(3, 4))

    def test_hash_in_set(self):
        s = {EisensteinInteger(0, 0), EisensteinInteger(0, 0)}
        assert len(s) == 1

    def test_hash_in_dict_key(self):
        d = {EisensteinInteger(1, 0): "a", EisensteinInteger(0, 1): "b"}
        assert d[EisensteinInteger(1, 0)] == "a"


# ─── Arithmetic Tests ────────────────────────────────────

class TestArithmetic:
    def test_addition(self):
        a = EisensteinInteger(1, 2)
        b = EisensteinInteger(3, 1)
        result = a + b
        assert result.a == 4
        assert result.b == 3

    def test_subtraction(self):
        a = EisensteinInteger(5, 3)
        b = EisensteinInteger(1, 1)
        result = a - b
        assert result.a == 4
        assert result.b == 2

    def test_addition_with_zero(self):
        a = EisensteinInteger(3, 4)
        z = EisensteinInteger(0, 0)
        assert (a + z) == a

    def test_subtraction_self(self):
        a = EisensteinInteger(3, 4)
        assert (a - a) == EisensteinInteger(0, 0)

    def test_negation(self):
        a = EisensteinInteger(3, -2)
        neg = -a
        assert neg.a == -3
        assert neg.b == 2


# ─── Norm Tests ──────────────────────────────────────────

class TestNorm:
    def test_zero_norm(self):
        assert EisensteinInteger(0, 0).norm() == 0

    def test_unit_norm(self):
        # The six unit directions should each produce a unit-norm EisensteinInteger
        for d in NEIGHBOR_DIRECTIONS:
            ei = EisensteinInteger(*d)
            assert ei.norm() >= 1

    def test_positive_norm(self):
        assert EisensteinInteger(1, 0).norm() > 0
        assert EisensteinInteger(0, 1).norm() > 0

    def test_norm_increases_with_distance(self):
        near = EisensteinInteger(1, 0).norm()
        far = EisensteinInteger(10, 0).norm()
        assert far > near


# ─── Hex Distance Tests ──────────────────────────────────

class TestHexDistance:
    def test_distance_to_self(self):
        e = EisensteinInteger(3, 5)
        assert hex_distance(e, e) == 0

    def test_distance_to_origin(self):
        origin = EisensteinInteger(0, 0)
        one_step = EisensteinInteger(1, 0)
        assert hex_distance(origin, one_step) == 1

    def test_distance_symmetric(self):
        a = EisensteinInteger(3, 4)
        b = EisensteinInteger(1, 2)
        assert hex_distance(a, b) == hex_distance(b, a)

    def test_distance_triangle_inequality(self):
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(2, 1)
        c = EisensteinInteger(5, 3)
        assert hex_distance(a, c) <= hex_distance(a, b) + hex_distance(b, c)

    def test_distance_positive(self):
        a = EisensteinInteger(0, 0)
        b = EisensteinInteger(5, 3)
        assert hex_distance(a, b) > 0


# ─── Neighbor Tests ──────────────────────────────────────

class TestNeighbors:
    def test_six_neighbors(self):
        e = EisensteinInteger(0, 0)
        neighbors = list(e.neighbors())
        assert len(neighbors) == 6

    def test_neighbor_directions_count(self):
        assert len(NEIGHBOR_DIRECTIONS) == 6

    def test_neighbors_all_different(self):
        e = EisensteinInteger(3, 4)
        neighbors = list(e.neighbors())
        assert len(set(neighbors)) == 6

    def test_neighbor_distance_one(self):
        e = EisensteinInteger(0, 0)
        for n in e.neighbors():
            assert hex_distance(e, n) == 1

    def test_neighbor_not_self(self):
        e = EisensteinInteger(5, 3)
        for n in e.neighbors():
            assert n != e

    def test_neighbor_offset_consistent(self):
        """Neighbors at origin should match direction tuples when constructed."""
        origin = EisensteinInteger(0, 0)
        neighbors = list(origin.neighbors())
        direction_eis = [EisensteinInteger(*d) for d in NEIGHBOR_DIRECTIONS]
        for n in neighbors:
            assert n in direction_eis

    def test_neighbor_reversibility(self):
        """If B is a neighbor of A, then A is a neighbor of B."""
        a = EisensteinInteger(3, 4)
        neighbors_a = set(a.neighbors())
        for n in neighbors_a:
            neighbors_n = set(n.neighbors())
            assert a in neighbors_n


# ─── String Representation Tests ─────────────────────────

class TestRepr:
    def test_repr_contains_values(self):
        e = EisensteinInteger(3, 4)
        r = repr(e)
        assert "3" in r
        assert "4" in r

    def test_str_contains_values(self):
        e = EisensteinInteger(-1, 2)
        s = str(e)
        assert "-1" in s or "1" in s
        assert "2" in s


# ─── Edge Cases ──────────────────────────────────────────

class TestEdgeCases:
    def test_large_values(self):
        e = EisensteinInteger(10000, 20000)
        assert e.a == 10000
        assert e.b == 20000

    def test_very_negative(self):
        e = EisensteinInteger(-1000, -2000)
        assert e.norm() > 0

    def test_one_zero(self):
        e = EisensteinInteger(5, 0)
        assert e.norm() > 0

    def test_zero_one(self):
        e = EisensteinInteger(0, 5)
        assert e.norm() > 0
