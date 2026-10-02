# Changelog

## [0.1.1] — Hex-line exactness + conformance receipts

- **Property suite completed (wave-67d, branch `fix/hex-distance-consistency`)**: the
  two mission properties the suite still lacked are now pinned in
  `tests/test_hex_distance_properties.py` — (P6) the triangle inequality
  `d(a,c) ≤ d(a,b) + d(b,c)`, grid-sampled exhaustively over radius-2 balls around
  five centers (34,295 ordered triples) plus a seeded random sample over the ±12 box,
  plus geodesic equality `d(a,c) == d(a,b) + d(b,c)` for every interior point of exact
  `hex_line` paths; (P7) the ring law `|ring_k| == 6k` for k ≥ 1 (origin + offset
  centers), `ring_1 == neighbors()` exactly, and the cumulative ball law
  `|rings(k)| == 1 + 3k(k+1)` with `rings(k) ∖ rings(k−1) == ring_k`. No runtime code
  changed — `hex_distance` was already the canonical cube form on main (wave-74d).
  Discrimination evidence in `receipts/bug-main.txt`: 67-d's independently written iff
  probe is RED against the published 0.1.0 artifact (worktree of `5bff9a3`: 4/61
  origin cells violate the iff; ring_1 picks up (1,−1)/(−1,1) and misses (1,1)/(−1,−1))
  and GREEN on main — the metric-law properties (P6, P7a, P7c) pass under BOTH formulas
  (the published formula is a genuine metric of the other convention), so P1/P7b are
  what pin the convention. 178 → 185 tests. README badges aligned (version 0.1.0 →
  0.1.1 per pyproject/`__init__`, tests 127 → 185). Version stays at the unreleased
  0.1.1; no version burned.

- **hex_distance ↔ neighbors() inconsistency FOUND and pinned — it lived in the published
  PyPI 0.1.0 artifact (wave-74d).** Git forensics: the initial publish commit `5bff9a3`
  ("📦 Published to PyPI + cleanup") shipped `hex_distance = max(|da|, |db|, |da+db|)` —
  the textbook axial formula, which is the correct graph distance for the OTHER axial
  neighbor set {(±1,0),(0,±1),(1,−1),(−1,1)} and wrong for this package's neighbor set
  {(±1,0),(0,±1),±(1,1)} (the units ±1, ±ω, ±(1+ω) of ℤ[ω]). On that artifact the
  "dist(a,b)==1 iff b ∈ neighbors(a)" property fails in 192 of the 3,721 ordered pairs of
  the radius-4 ball (88 true neighbors scored ≠ 1 — every ±(1+ω) step scored 2; 104
  non-neighbors scored 1 — every (1,−1)/(−1,1) diagonal scored 1). Symmetry, notably,
  holds even in the buggy formula — the defect is an iff violation, not an asymmetry.
  The correction already sat unversioned in the repo tree (commit `2946624`, inside a
  "Published to PyPI + cleanup" commit, no changelog mention) — which is why the 67-a
  brute-force audit below could not reproduce it against the repo. This lane:
  (1) `hex_distance` is now the self-evident canonical cube form
  `( |da| + |db−da| + |db| ) // 2` (== the old same-sign/opposite-sign branches; behavior
  byte-identical), with the convention trap documented in the docstring;
  (2) `tests/test_hex_distance_properties.py` — exhaustive property suite over the
  radius-4 neighborhood: dist==1 iff neighbor (both directions), symmetry over all pairs,
  exact cube-form identity, BFS-graph-distance agreement, and the published-0.1.0 formula
  vendored + pinned (witnesses E(0,0)→E(1,1) and E(0,0)→E(1,−1), exact 192-violation
  count) so the published formula cannot return unnoticed;
  (3) honest RED run receipted: the new suite scores **11 failed / 2 passed against the
  published 0.1.0 artifact** (worktree of `5bff9a3`), green against the fixed tree
  (`receipts/red-state-74d.txt`);
  (4) `lua_port.lua` comment repaired (the Luau code was correct; its docstring described
  the buggy published formula).
  Version note: 0.1.1 was already claimed (unpublished) by the 67-a lane; this lane folds
  into the same unreleased 0.1.1 rather than burning 0.1.2.
- **Fixed `hex_line` (geometry.py)**: replaced the float Cartesian lerp + snap
  interpolation with an exact integer cube-coordinate line draw. On v0.1.0,
  60,376 of 390,000 ordered pairs in the ±12 box produced consecutive line
  points at hex distance 2 (the mid sample of a 1−ω-diagonal segment tied
  between two lattice points under banker's rounding and could snap back onto
  an endpoint — e.g. `hex_line(E(0,0), E(1,−1))` lost its middle point). The
  new algorithm guarantees exact endpoints, length exactly
  `hex_distance(start, goal) + 1`, consecutive points at hex distance exactly 1,
  and platform-independent output. Deterministic tie-break documented in the
  docstring and TEST-RECEIPT.md (half-up rounding; deviation ties re-derive
  cube z).
- **Six-step conformance suite added** (tests/test_eisenstein.py,
  TestSixStepConformance): for every canonical unit step u ∈ {±1, ±ω, ±(1+ω)}:
  N(u) = 1, hex_distance(a, a+u) = 1, neighbors(a) contains a+u, Cartesian
  round-trip holds, plus BFS-graph-distance == hex_distance over a box.
  Honest finding: the wave-66 claim that hex_distance and neighbors() disagree
  at ±(1+ω) did NOT reproduce on v0.1.0 — the suite is green against the
  unmodified v0.1.0 arithmetic and is retained as a regression guard, not a fix.
  [wave-74d correction: it did not reproduce *in the repo tree* because the fix
  had already landed unversioned in `2946624`; the claim was true of the published
  PyPI 0.1.0 artifact (`5bff9a3`) — see the first bullet.]
- **CI workflows repaired** (.github/workflows/ci.yml, tests.yml): install the
  package itself with `python -m pip install -e ".[dev]"` — ci.yml previously
  guarded the editable install behind `[ -f setup.py ]`, which never fires in
  this pyproject.toml-only repo (tests passed only via CWD-import accident);
  tests.yml no longer masks install failures with `2>/dev/null || true`.
- **TEST-RECEIPT.md added**: run-verified pytest counts (127 baseline →
  12 failed/26 passed RED → 165 passed GREEN), the 12 failing-then-passing test
  names, the six-step conformance table, and the hex_line tie-break of record.
  RED-state output preserved at receipts/red-state-67a.txt. [wave-74d adds
  receipts/red-state-74d.txt: 13 new property tests, 11 failed/2 passed against
  the published 0.1.0 artifact, 178 passed after the canonical-form pin.]

## [0.1.0] - Initial Release

- Lattice coordination primitives for multi-agent systems
- Python package (this repo publishes to PyPI as `slackwater-lattice`; the crates.io Rust twin lives at [slackwater-rust](https://github.com/SuperInstance/slackwater-rust))
- Engineering manual README with full API reference
- 127 tests, all passing
