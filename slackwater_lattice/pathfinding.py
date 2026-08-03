"""
Pathfinding through the Eisenstein lattice.

Plans paths through occupied and free lattice points using the
hexagonal neighbor graph. A* search with exact integer heuristics.

The lattice gives us something square grids cannot: every step
is the same length, in every direction. There is no diagonal
penalty, no cardinal preference. The shortest path is the one
that goes straight, and straight on a hex grid is beautiful.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Optional

from slackwater_lattice.eisenstein import (
    EisensteinInteger,
    hex_distance,
    NEIGHBOR_DIRECTIONS,
)
from slackwater_lattice.placement import BuildPlacement


@dataclass
class LatticePath:
    """A path through the lattice as an ordered list of points."""
    points: list[EisensteinInteger]

    def length(self) -> int:
        """Number of steps (edges) in the path."""
        return max(0, len(self.points) - 1)

    def is_empty(self) -> bool:
        return len(self.points) <= 1

    def __iter__(self):
        return iter(self.points)

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, idx: int) -> EisensteinInteger:
        return self.points[idx]

    def __repr__(self) -> str:
        return f"LatticePath({' → '.join(str(p) for p in self.points)})"


@dataclass
class LatticePathfinder:
    """
    A* pathfinder on the Eisenstein lattice.

    Attributes:
        placement: The BuildPlacement managing occupied/free points.
        allow_diagonal_through: If True, paths can pass through
            occupied points (useful for aerial paths). Default False.
    """

    placement: BuildPlacement
    allow_through_occupied: bool = False

    def find_path(
        self,
        start: EisensteinInteger,
        goal: EisensteinInteger,
        max_steps: int = 10_000,
    ) -> Optional[LatticePath]:
        """
        Find the shortest path from start to goal through free lattice points.

        Uses A* with hex_distance as the heuristic — which is admissible
        and consistent on the hexagonal neighbor graph, guaranteeing
        optimal paths.

        Returns None if no path exists within max_steps expansions.
        """
        if start == goal:
            return LatticePath([start])

        # If goal is occupied and we can't pass through, fail fast
        if not self.allow_through_occupied:
            if self.placement.check_collision(goal):
                return None

        # A* search
        open_heap: list[tuple[int, int, EisensteinInteger]] = []
        counter = 0  # tiebreaker for heapq stability
        heapq.heappush(open_heap, (hex_distance(start, goal), counter, start))

        came_from: dict[EisensteinInteger, EisensteinInteger] = {}
        g_score: dict[EisensteinInteger, int] = {start: 0}
        closed: set[EisensteinInteger] = set()
        expansions = 0

        while open_heap:
            _, _, current = heapq.heappop(open_heap)

            if current == goal:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return LatticePath(path)

            if current in closed:
                continue
            closed.add(current)

            expansions += 1
            if expansions > max_steps:
                return None

            for neighbor in current.neighbors():
                if neighbor in closed:
                    continue

                # Check passability
                if not self.allow_through_occupied:
                    if neighbor != goal and self.placement.check_collision(neighbor):
                        continue
                elif self.placement.check_collision(neighbor) and neighbor != goal:
                    # Even with allow_through, we prefer free paths
                    pass

                tentative_g = g_score[current] + 1

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + hex_distance(neighbor, goal)
                    counter += 1
                    heapq.heappush(open_heap, (f, counter, neighbor))

        return None  # No path found

    def find_all_paths(
        self,
        start: EisensteinInteger,
        goal: EisensteinInteger,
        max_paths: int = 5,
    ) -> list[LatticePath]:
        """
        Find up to `max_paths` shortest paths using Yen's algorithm (simplified).

        Useful when you want alternatives — the primary path and backups.
        """
        paths: list[LatticePath] = []
        primary = self.find_path(start, goal)
        if primary is None:
            return paths
        paths.append(primary)

        # Simplified k-shortest: try variations by blocking each edge
        for i in range(len(primary.points) - 1):
            if len(paths) >= max_paths:
                break
            spur_node = primary.points[i]
            next_node = primary.points[i + 1]

            # Temporarily block the edge by occupying next_node
            was_free = next_node not in self.placement.occupied
            if was_free:
                self.placement.reserve(next_node, {"_yen_block": True})

            alt = self.find_path(spur_node, goal)
            if alt is not None:
                # Prepend the prefix
                prefix = primary.points[:i]
                full = LatticePath(prefix + alt.points)
                if full not in paths:
                    paths.append(full)

            # Restore
            if was_free:
                self.placement.release(next_node)

        return paths

    def reachable(
        self,
        start: EisensteinInteger,
        max_distance: int = 20,
    ) -> dict[EisensteinInteger, int]:
        """
        BFS to find all reachable free points within max_distance steps.
        Returns a dict of {point: distance}.
        """
        visited: dict[EisensteinInteger, int] = {start: 0}
        frontier: list[EisensteinInteger] = [start]

        while frontier:
            current = frontier.pop(0)
            dist = visited[current]
            if dist >= max_distance:
                continue
            for neighbor in current.neighbors():
                if neighbor in visited:
                    continue
                if neighbor != start and self.placement.check_collision(neighbor):
                    continue
                visited[neighbor] = dist + 1
                frontier.append(neighbor)

        del visited[start]  # Don't include start itself
        return visited
