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
