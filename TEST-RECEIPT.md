# TEST-RECEIPT — task 67-a (wave 67, lane a)

Repo: SuperInstance/slackwater-lattice · lane: 67-a upstream repair (v0.1.1)
All numbers below are run-verified on this lane. No token or credential material appears in this receipt.

## Environment of record

- Python: 3.12.14 (`/home/z/.venv/bin/python3`)
- pytest: 9.0.2
- Platform: Linux (container), repo at `/home/z/my-project/study/slackwater-lattice`
- Baseline commit (v0.1.0): `6e429661b37e7a66e220793afdccddedbee0e1a5`

## pytest counts

| stage | command | result |
|---|---|---|
| baseline (v0.1.0, before any edit) | `python3 -m pytest -q` | **127 passed** in 0.33s |
| RED — new conformance tests added, fix NOT yet applied | `python3 -m pytest tests/test_geometry.py::TestHexLineExact tests/test_eisenstein.py::TestSixStepConformance -v` | **12 failed, 26 passed** in 0.23s (full output: `receipts/red-state-67a.txt`) |
| GREEN — full suite after fix | `python3 -m pytest -q` | **165 passed** in 0.42s |

Net: +38 tests (24 parametrized six-step conformance + 2 conformance unit tests + 12 hex_line exactness tests). 127 → 165.

## Defect verdicts (wave-66 claims, independently verified this lane)

1. **hex_distance vs neighbors() disagree at ±(1+ω) — NOT REPRODUCED (no fix invented).**
   Brute-force audit of v0.1.0 code: for all 169 points in the ±6 box × 6 canonical unit steps
   (1,014 checks), `hex_distance(a, a+u) == 1` held for every step including ±(1+ω) = ±(1,1);
   `neighbors(a)` returned exactly the six norm-1 units everywhere; BFS graph distance over
   `neighbors()` equals `hex_distance` for all 217 bounded points from two different origins;
   every canonical step has Eisenstein norm N = a²−ab+b² = 1 (a true unit of ℤ[ω]) and survives
   the Cartesian round-trip. The hex_distance formula (same-sign → max(|da|,|db|), opposite-sign
   → |da|+|db|) is the correct axial hex distance for this neighbor set. The six-step conformance
   suite was added anyway and is green from the RED stage onward — it is a regression guard, not
   a fix. Note the conformance table below was green *before* any production change.
2. **CI YAML — PARTIALLY REAL (fixed).** Both `.github/workflows/ci.yml` and `tests.yml` parse
   (`yaml.safe_load`) and have correct `on:` push/PR triggers, `runs-on`, checkout/setup-python
   actions, and a pytest invocation — so "broken YAML" was overstated. The real defects:
   ci.yml guarded `pip install -e .` behind `[ -f setup.py ]`, but this repo has **no setup.py**
   (pyproject.toml-only), so the package was never installed in CI (tests only passed via CWD
   import accident); tests.yml masked install failures with `2>/dev/null || true`. Both now run
   `python -m pip install -e ".[dev]"` unmasked. Validation: both files parse and carry
   triggers/runner/python/pytest/install (structural check run on this lane, ALL OK).
3. **Missing run receipt — REAL (fixed by this file).**
4. **hex_line float interpolation — REAL (fixed).** v0.1.0 `hex_line` lerped in Cartesian floats
   and snapped each sample with `from_cartesian` (Python banker's rounding). For segments whose
   midpoint lands on a hexagon edge (offsets like (1,−1), the 1−ω diagonal), the mid sample tied
   between two lattice points and could snap back onto an endpoint — the middle point was
   dropped. Brute force over the ±12 box on v0.1.0: **60,376 of 390,000 ordered pairs produced
   consecutive points at hex distance 2; 33,684 had wrong length; smallest witness
   `hex_line(E(0,0), E(1,−1))` (d=2) returned 2 points instead of 3.** Endpoints and monotonicity
   never failed. Replaced with an exact integer cube-coordinate line draw; after the fix the same
   ±12-box brute force reports **0 endpoint failures, 0 length failures, 0 non-neighbor gaps,
   0 non-monotone lines over 390,000 pairs** (±6 box recheck: 0/28,392).

## Failing-then-passing test names (the 12 RED → GREEN)

```
tests/test_geometry.py::TestHexLineExact::test_consecutive_points_are_hex_neighbors[start0-goal0]
tests/test_geometry.py::TestHexLineExact::test_consecutive_points_are_hex_neighbors[start1-goal1]
tests/test_geometry.py::TestHexLineExact::test_consecutive_points_are_hex_neighbors[start2-goal2]
tests/test_geometry.py::TestHexLineExact::test_consecutive_points_are_hex_neighbors[start3-goal3]
tests/test_geometry.py::TestHexLineExact::test_consecutive_points_are_hex_neighbors[start4-goal4]
tests/test_geometry.py::TestHexLineExact::test_line_length_is_distance_plus_one[start0-goal0]
tests/test_geometry.py::TestHexLineExact::test_line_length_is_distance_plus_one[start1-goal1]
tests/test_geometry.py::TestHexLineExact::test_line_length_is_distance_plus_one[start2-goal2]
tests/test_geometry.py::TestHexLineExact::test_line_length_is_distance_plus_one[start3-goal3]
tests/test_geometry.py::TestHexLineExact::test_line_length_is_distance_plus_one[start4-goal4]
tests/test_geometry.py::TestHexLineExact::test_tie_break_deterministic
tests/test_geometry.py::TestHexLineExact::test_all_pairs_small_box_are_valid_lines
```

(RED_CASES witnesses, all verified failing on v0.1.0: E(0,0)→E(1,−1), E(1,1)→E(2,0),
E(−2,0)→E(−3,1), E(−3,2)→E(0,1), E(−3,3)→E(0,0).)

## Six-step conformance table (live run, a = origin)

| step u (da, db) | N(u) | hex_distance(0, u) | u ∈ neighbors(0) | Cartesian round-trip |
|---|---|---|---|---|
| (1, 0)   | 1 | 1 | True | True |
| (−1, 0)  | 1 | 1 | True | True |
| (0, 1)   | 1 | 1 | True | True |
| (0, −1)  | 1 | 1 | True | True |
| (1, 1)   | 1 | 1 | True | True |
| (−1, −1) | 1 | 1 | True | True |

(1,1) and (−1,−1) are the ±(1+ω) steps named by wave-66 — they conform. Full probe:
169 points, 1,014 unit-step checks, 217 BFS points, **0 failures**.

## hex_line algorithm of record (v0.1.1) and tie-break

Cube coordinates (x, y, z) = (a, b−a, −b) (x+y+z = 0; the six neighbor steps become unit cube
steps). For i = 0..d (d = hex_distance), the lerp numerators are exact integers over the common
denominator d. Each component rounds **half-up (ties toward +∞)**: `round_half_up(num, den) =
(2·num + den) // (2·den)`. The component with the largest rounding deviation is then re-derived
from the other two so x+y+z = 0 exactly; on equal deviations the check order x → y → z means z is
re-derived — that is the deterministic tie-break. Consequences: endpoints exact, length exactly
d+1, consecutive points at hex distance exactly 1, identical output on every platform. Pinned
example (test_tie_break_deterministic): E(0,0)→E(1,−1) = [E(0,0), E(1,0), E(1,−1)].

---

# ADDENDUM — wave-74d: the published PyPI 0.1.0 hex_distance defect, found and pinned

The 67-a verdict above ("NOT REPRODUCED") was true of the repo tree and needs a
correction of record: the defect was real in the **published PyPI 0.1.0 artifact**.
Git forensics on this lane:

- Commit `5bff9a3` ("📦 Published to PyPI + cleanup") shipped
  `hex_distance = max(|da|, |db|, |da+db|)` — the textbook axial formula, correct for the
  OTHER axial neighbor set {(±1,0),(0,±1),(1,−1),(−1,1)}, wrong for this package's
  {(±1,0),(0,±1),±(1,1)}. The correction (same-sign → max, opposite-sign → sum) landed
  unversioned in the next commit `2946624` with no changelog mention — hence 67-a's
  non-reproduction against the repo baseline `6e42966`.
- Measured on the `5bff9a3` artifact (radius-4 ball around the origin, 61 points,
  3,721 ordered pairs): **192 iff-violations** of "dist(a,b)==1 iff b ∈ neighbors(a)"
  (88 true neighbors scored ≠ 1 — every ±(1+ω) step scored 2; 104 non-neighbors scored
  1 — every (1,−1)/(−1,1) diagonal scored 1). **Symmetry holds even in the buggy
  formula** — the defect is an iff violation, not an asymmetry (the 2 symmetry tests
  pass in the RED run below).
- RED (worktree of `5bff9a3`, new suite only): **11 failed / 2 passed** —
  `receipts/red-state-74d.txt`.
- GREEN (fixed tree, full suite): **178 passed** (165 prior + 13 new property tests in
  `tests/test_hex_distance_properties.py`: iff both directions, symmetry over all pairs,
  exact cube-form identity `( |da| + |db−da| + |db| ) // 2`, BFS agreement from two
  sources, and the published formula vendored + pinned with witnesses E(0,0)→E(1,1)
  (neighbor, buggy 2) and E(0,0)→E(1,−1) (non-neighbor, buggy 1) and the exact
  192-violation count).
- Production change this lane: `hex_distance` rewritten to the canonical cube form
  (byte-identical behavior, branch-free), convention trap documented in the docstring;
  `lua_port.lua` docstring repaired (code was correct, comment described the buggy
  formula). Version stays at the unreleased 0.1.1 (67-a's claim); no 0.1.2 burned.

---

# ADDENDUM 2 — wave-67d (task 67-d): property suite completed, stale-scout-list audit

Branch `fix/hex-distance-consistency` (PR lane; no direct push to main). All numbers
run-verified this lane. Environment: Python 3.12.14, pytest 9.0.2, Linux container.

## What this lane found

The sprint-1 scout item ("hex_distance and neighbors() disagree by ±(1+ω) — test
fails on main") was STALE: main @ 94a7f2b already contains the canonical cube-form
`hex_distance` (landed unversioned in `2946624`, pinned by wave-74d in `94a7f2b`).
A freshly written iff probe (`receipts/bug-main.txt`, source verbatim therein) was
run FIRST, before any edit:

| state | probe result |
|---|---|
| worktree of `5bff9a3` (published PyPI 0.1.0 — what main shipped at sprint-1) | **RED** — 4 of 61 origin cells violate `hex_distance(o,c)==1 ⟺ c ∈ neighbors(o)` (±(1+ω) neighbors scored 2; (1,−1)/(−1,1) diagonals scored 1); pytest: 1 failed |
| main @ 94a7f2b == this branch's base | **GREEN** — 0 violations |

Property-discrimination table (receipts/bug-main.txt): under the published formula,
P1 iff and P7b ring_1==neighbors FAIL while P6 triangle, P7a |ring_k|==6k, and P7c
cumulative ball law PASS — the published formula is a genuine metric of the OTHER
axial convention, so only the convention-tied properties catch the defect.

## pytest counts (this lane)

| stage | command | result |
|---|---|---|
| baseline (main 94a7f2b, before edits) | `python3 -m pytest -q` | **178 passed** |
| GREEN after additions | `python3 -m pytest -q` | **185 passed** (0 warnings) |

Net +7 tests, all in `tests/test_hex_distance_properties.py`:
- `TestTriangleInequality` (3): exhaustive triangle inequality over radius-2 balls
  around five centers (5 × 19³ = 34,295 ordered triples); seeded (random.Random(67))
  sample over the ±12 box (300 points × 10 random pairs each); geodesic equality
  along exact `hex_line` paths (d(a,c) == d(a,b)+d(b,c) for every interior b, with
  line length == d+1 re-asserted).
- `TestRingLaw` (4): |hex_ring(c,k)| == 6k for k=1..8 at the origin and k=1..5 at
  four offset centers (with exact-distance check per point); ring_1 == neighbors()
  exactly at five centers (the convention-tied property — RED against the published
  formula per receipts/bug-main.txt); cumulative ball law |rings(k)| == 1+3k(k+1)
  for k=1..6 with rings(k) ∖ rings(k−1) == ring_k and |ball(k)| == 1+3k(k+1).

No runtime code changed. `hex_distance` was NOT touched — the minimal fix was
already on main; redesigning it again would have been churn, not repair.

## Version note

pyproject.toml and `slackwater_lattice.__version__` already say 0.1.1 (unreleased,
claimed by 67-a/74-d). This lane changes no runtime behavior; the PR folds into the
same unreleased 0.1.1. README's version badge was stale (0.1.0) and the tests badge
was stale (127, pre-74d) — both aligned (0.1.1 / 185). The published PyPI 0.1.0
artifact remains the buggy one; the maintainer lane should cut the 0.1.1 release
from main + this PR so the published wheel stops shipping the wrong-convention
`hex_distance`.
