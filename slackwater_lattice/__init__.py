"""
slackwater-lattice: Exact integer geometry on the Eisenstein A₂ hexagonal lattice.

The densest packing of circles in a plane. Every point has exactly six
equidistant neighbors. No privileged axis. No floating-point drift.

    >>> from slackwater_lattice import EisensteinInteger, BuildPlacement
    >>> z = EisensteinInteger(3, 1)
    >>> z.neighbors()
    [4+w, 3+2w, 2+2w, 2+w, 3+0w, 4+0w]

The lattice does not vote. The lattice does not compromise.
The lattice finds the shape that was always there.
"""

from slackwater_lattice.eisenstein import EisensteinInteger, EISENSTEIN_OMEGA
from slackwater_lattice.placement import BuildPlacement
from slackwater_lattice.pathfinding import LatticePathfinder

__all__ = [
    "EisensteinInteger",
    "EISENSTEIN_OMEGA",
    "BuildPlacement",
    "LatticePathfinder",
]

__version__ = "0.1.0"
