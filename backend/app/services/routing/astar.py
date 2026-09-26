from heapq import heappop, heappush
from math import hypot, inf
from collections.abc import Callable

Point = tuple[int, int]


class RouteError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def astar(grid: list[list[dict]], start: Point, destination: Point, step_cost: Callable[[Point, Point, float], float]) -> list[Point]:
    rows, cols = len(grid), len(grid[0])
    for point, name in ((start, "START"), (destination, "DESTINATION")):
        row, col = point
        if not (0 <= row < rows and 0 <= col < cols):
            raise RouteError(f"INVALID_{name}", f"{name.title()} is outside the demo grid")
        if not grid[row][col]["navigable"]:
            raise RouteError(f"BLOCKED_{name}", f"{name.title()} is non-navigable at the simulated depth threshold")
    if start == destination:
        return [start]
    queue = [(hypot(destination[0] - start[0], destination[1] - start[1]), 0.0, start)]
    distances = {start: 0.0}
    previous: dict[Point, Point] = {}
    while queue:
        _, known_cost, point = heappop(queue)
        if known_cost > distances[point] + 1e-9:
            continue
        if point == destination:
            path = [point]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return path[::-1]
        row, col = point
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if not (0 <= nr < rows and 0 <= nc < cols) or not grid[nr][nc]["navigable"]:
                    continue
                # Prevent a diagonal from slipping between two blocked cells.
                if dr and dc and (not grid[row + dr][col]["navigable"] or not grid[row][col + dc]["navigable"]):
                    continue
                neighbor = (nr, nc)
                candidate = known_cost + step_cost(point, neighbor, hypot(dr, dc))
                if candidate + 1e-9 < distances.get(neighbor, inf):
                    distances[neighbor] = candidate
                    previous[neighbor] = point
                    heuristic = hypot(destination[0] - nr, destination[1] - nc)
                    heappush(queue, (candidate + heuristic, candidate, neighbor))
    raise RouteError("NO_PATH", "No navigable path exists between these endpoints")
