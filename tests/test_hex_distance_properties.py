"""
Exhaustive hex_distance ↔ neighbors() property suite (wave-74d).

Two properties over the radius-4 neighborhood of the origin (61 points,
3,721 ordered pairs), plus the canonical-form identity and a pinned
regression witness against the PUBLISHED PyPI 0.1.0 formula.

Properties:
  P1  dist(a, b) == 1  IFF  b ∈ neighbors(a)          (both directions, all pairs)
  P2  dist(a, b) == dist(b, a)                        (symmetry, all pairs)
  P3  dist(a, b) == (|da| + |db−da| + |db|) // 2      (exact cube-coordinate distance;
                                                       this package's cube map is
                                                       (x, y, z) = (a, b−a, −b), which
                                                       turns the six canonical unit steps
                                                       ±(1,0), ±(0,1), ±(1,1) into unit
                                                       cube steps)
  P4  BFS graph distance over neighbors() == dist     (all pairs, both inside a radius-4
                                                       ball; BFS run on a radius-8 box so
                                                       shortest paths never leave the box)

The published PyPI 0.1.0 artifact (commit 5bff9a3) shipped

    d = max(|da|, |db|, |da + db|)

— the textbook axial formula, which is correct for the OTHER axial neighbor
set {(±1,0), (0,±1), (1,−1), (−1,1)} but WRONG for this package's neighbor set
{(±1,0), (0,±1), ±(1,1)} (the units ±1, ±ω, ±(1+ω) of ℤ[ω]). Misapplied, it
scores every ±(1+ω) step (1,1)/(−1,−1) — which IS a neighbor step — as 2, and
scores the (1,−1)/(−1,1) diagonal — which is NOT a neighbor step — as 1. That
is exactly the "hex_distance / neighbors() inconsistent at ±(1+ω)" defect of
the published 0.1.0 wheel. P5 pins the witnesses so a regression to the
published formula cannot pass this suite.
"""

import pytest

from slackwater_lattice.eisenstein import EisensteinInteger, hex_distance

ORIGIN = EisensteinInteger(0, 0)

# The published PyPI 0.1.0 formula, vendored verbatim from commit 5bff9a3
# ("📦 Published to PyPI + cleanup") so the defect stays pinned and demonstrable
# without network access to PyPI.
def pypi_0_1_0_hex_distance(a: EisensteinInteger, b: EisensteinInteger) -> int:
    da = a.a - b.a
    db = a.b - b.b
    return max(abs(da), abs(db), abs(da + db))


def ball(radius: int) -> list[EisensteinInteger]:
    """All lattice points within `radius` hex steps of the origin."""
    out = []
    for da in range(-radius, radius + 1):
        for db in range(-radius, radius + 1):
            p = EisensteinInteger(da, db)
            if hex_distance(ORIGIN, p) <= radius:
                out.append(p)
    return out


R4 = ball(4)
R4_PAIRS = [(a, b) for a in R4 for b in R4]


def bfs_distances(sources: list[EisensteinInteger], bound_box: int = 8) -> dict:
    """Multi-source BFS over neighbors(), bounded to the ±bound_box box."""
    from collections import deque

    dist = {}
    q = deque()
    for s in sources:
        dist[s] = 0
        q.append(s)
    while q:
        cur = q.popleft()
        for n in cur.neighbors():
            if max(abs(n.a), abs(n.b)) > bound_box:
                continue
            if n not in dist:
                dist[n] = dist[cur] + 1
                q.append(n)
    return dist


class TestDistOneIffNeighbor:
    """P1: dist(a,b)==1 iff b ∈ neighbors(a), over every ordered pair in the ball."""

    def test_dist_one_iff_neighbor(self):
        bad = []
        for a, b in R4_PAIRS:
            nb = a in R4 and b in set(a.neighbors())
            d1 = hex_distance(a, b) == 1
            if nb != d1:
                bad.append((a, b, hex_distance(a, b), nb))
        assert not bad, f"{len(bad)} pairs violate dist==1 iff neighbor; first: {bad[0]}"

    def test_every_neighbor_is_at_distance_one(self):
        for a in R4:
            for n in a.neighbors():
                assert hex_distance(a, n) == 1, f"neighbor {n} of {a} at distance {hex_distance(a, n)}"

    def test_every_distance_one_pair_is_a_neighbor(self):
        for a in R4:
            for b in R4:
                if hex_distance(a, b) == 1:
                    assert b in set(a.neighbors()), f"{b} at distance 1 from {a} but not a neighbor"


class TestSymmetry:
    """P2: dist(a,b) == dist(b,a) over every ordered pair in the ball."""

    def test_symmetry_all_pairs(self):
        bad = [(a, b) for a, b in R4_PAIRS if hex_distance(a, b) != hex_distance(b, a)]
        assert not bad, f"{len(bad)} asymmetric pairs; first: {bad[0]}"

    def test_symmetry_off_center(self):
        # same property anchored away from the origin (centers on 4 arbitrary points)
        for c in [EisensteinInteger(2, -1), EisensteinInteger(-3, 3), EisensteinInteger(0, 4), EisensteinInteger(1, 1)]:
            pts = [c + EisensteinInteger(p.a, p.b) for p in ball(3)]
            for a in pts:
                for b in pts:
                    assert hex_distance(a, b) == hex_distance(b, a)


class TestCanonicalCubeForm:
    """P3: the implementation IS the exact cube-coordinate distance."""

    def test_equals_cube_formula_all_pairs(self):
        bad = []
        for a, b in R4_PAIRS:
            da, db = a.a - b.a, a.b - b.b
            cube = (abs(da) + abs(db - da) + abs(db)) // 2
            if hex_distance(a, b) != cube:
                bad.append((a, b, hex_distance(a, b), cube))
        assert not bad, f"{len(bad)} pairs disagree with the cube formula; first: {bad[0]}"

    def test_known_distances(self):
        assert hex_distance(ORIGIN, EisensteinInteger(3, 0)) == 3
        assert hex_distance(ORIGIN, EisensteinInteger(0, 3)) == 3
        assert hex_distance(ORIGIN, EisensteinInteger(3, 3)) == 3    # same-sign sector
        assert hex_distance(ORIGIN, EisensteinInteger(1, 1)) == 1    # ±(1+ω): a neighbor step
        assert hex_distance(ORIGIN, EisensteinInteger(2, -1)) == 3   # opposite sign
        assert hex_distance(ORIGIN, EisensteinInteger(1, -1)) == 2   # NOT a neighbor step


class TestBfsAgreement:
    """P4: graph distance over neighbors() == hex_distance inside the ball."""

    def test_bfs_matches_hex_distance(self):
        dist = bfs_distances([ORIGIN], bound_box=8)
        bad = []
        for b in R4:
            if b == ORIGIN:
                continue
            if dist.get(b) != hex_distance(ORIGIN, b):
                bad.append((b, hex_distance(ORIGIN, b), dist.get(b)))
        assert not bad, f"{len(bad)} BFS mismatches; first: {bad[0]}"

    def test_bfs_matches_from_off_center_source(self):
        src = EisensteinInteger(2, -2)
        dist = bfs_distances([src], bound_box=8)
        for b in ball(3):
            p = src + EisensteinInteger(b.a, b.b)
            if p == src:
                continue
            assert dist.get(p) == hex_distance(src, p), f"{p}: BFS {dist.get(p)} != hex {hex_distance(src, p)}"


class TestPublishedPyPI010BugIsPinned:
    """P5: the published 0.1.0 formula violates P1 exactly on the diagonal classes,
    and the witnesses stay fixed so the published formula can never come back."""

    def test_witness_neighbor_scored_two_by_published_formula(self):
        # (0,0) -> (1,1) is the ±(1+ω) step: a TRUE neighbor; published 0.1.0 scores it 2.
        b = EisensteinInteger(1, 1)
        assert b in set(ORIGIN.neighbors())
        assert hex_distance(ORIGIN, b) == 1
        assert pypi_0_1_0_hex_distance(ORIGIN, b) == 2, "published formula witness changed — re-pin against commit 5bff9a3"

    def test_witness_non_neighbor_scored_one_by_published_formula(self):
        # (0,0) -> (1,-1) is NOT a neighbor (true distance 2); published 0.1.0 scores it 1.
        b = EisensteinInteger(1, -1)
        assert b not in set(ORIGIN.neighbors())
        assert hex_distance(ORIGIN, b) == 2
        assert pypi_0_1_0_hex_distance(ORIGIN, b) == 1, "published formula witness changed — re-pin against commit 5bff9a3"

    def test_published_formula_violates_iff_property_on_the_ball(self):
        # The published formula fails P1 on this exact, counted set of pairs —
        # the defect is real in the published artifact, not a rumor.
        bad = []
        for a, b in R4_PAIRS:
            nb = b in set(a.neighbors())
            d1 = pypi_0_1_0_hex_distance(a, b) == 1
            if nb != d1:
                bad.append((a, b))
        # Off-axis pairs are the published formula's violations; the exact count
        # is a deterministic witness of the published artifact's defect.
        assert len(bad) == 192, f"iff-violation count changed: {len(bad)} (expected 192 over 3,721 pairs)"
        assert all((hex_distance(a, b) == 1) != (pypi_0_1_0_hex_distance(a, b) == 1) for a, b in bad)

    def test_current_formula_differs_from_published_only_off_axis(self):
        # The two formulas agree exactly when the offset is on a coordinate axis
        # (da == 0 or db == 0) and disagree on EVERY off-axis pair — the textbook
        # formula computes the true distance of the OTHER axial convention, so in
        # this package's convention it errs on all of da/db-space except the axes.
        agree_bad = []
        differing = []
        for a, b in R4_PAIRS:
            da, db = a.a - b.a, a.b - b.b
            cur, pub = hex_distance(a, b), pypi_0_1_0_hex_distance(a, b)
            if cur != pub:
                differing.append((da, db))
            elif not (da == 0 or db == 0):
                agree_bad.append((da, db, cur))
        assert differing, "fix does not differ from the published formula at all"
        assert not agree_bad, f"on-axis agreement violated: {agree_bad[:6]}"
        assert all(da != 0 and db != 0 for da, db in differing), \
            f"unexpected off-axis disagreement: {sorted(set(differing))[:6]}"
