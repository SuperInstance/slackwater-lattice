# Slackwater Lattice

*Build placement on the Eisenstein A₂ hexagonal lattice. Isotropic. Exact. Beautiful.*

A Python + Lua package that snaps all build placements to a hexagonal lattice. Guarantees minimum spacing, eliminates floating-point drift, and produces visually organic tidal-community architecture.

## What it does

- **EisensteinInteger**: exact arithmetic on the hexagonal lattice (no floats)
- **LatticeSnap**: snap any (x, z) position to the nearest lattice point
- **LatticeNeighbors**: find the 6 equidistant neighbors of any point
- **LatticePath**: plan a path through the lattice (for bridges, roads, conveyor belts)
- **LatticeDensity**: measure how dense a build is (harmony governor input)

## Why hexagonal?

Square grids have a 41% diagonal penalty — neighbors aren't equidistant. Hexagonal lattices have 6 equidistant neighbors at exactly distance 1. Agreement is isotropic. Error is uniform. The math is exact integer arithmetic, inspired by the FLUX constraint engine.

## Related

- [Snapkit v2](https://github.com/SuperInstance/snapkit-v2) — the triadic cognitive architecture this lattice supports
- [Constraint Theory Math](https://github.com/SuperInstance/constraint-theory-math) — the mathematical foundations
