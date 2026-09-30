# Changelog

## [0.1.1] — Hex-line exactness + conformance receipts

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
- **CI workflows repaired** (.github/workflows/ci.yml, tests.yml): install the
  package itself with `python -m pip install -e ".[dev]"` — ci.yml previously
  guarded the editable install behind `[ -f setup.py ]`, which never fires in
  this pyproject.toml-only repo (tests passed only via CWD-import accident);
  tests.yml no longer masks install failures with `2>/dev/null || true`.
- **TEST-RECEIPT.md added**: run-verified pytest counts (127 baseline →
  12 failed/26 passed RED → 165 passed GREEN), the 12 failing-then-passing test
  names, the six-step conformance table, and the hex_line tie-break of record.
  RED-state output preserved at receipts/red-state-67a.txt.

## [0.1.0] - Initial Release

- Lattice coordination primitives for multi-agent systems
- Python package (this repo publishes to PyPI as `slackwater-lattice`; the crates.io Rust twin lives at [slackwater-rust](https://github.com/SuperInstance/slackwater-rust))
- Engineering manual README with full API reference
- 127 tests, all passing
