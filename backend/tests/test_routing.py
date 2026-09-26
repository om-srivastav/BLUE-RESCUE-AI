from math import hypot

import pytest

from app.services.risk.config import RiskConfig
from app.services.risk.engine import build_risk_map, load_demo_environment
from app.services.routing.astar import RouteError, astar
from app.services.routing.service import calculate_routes


def fixture_grid():
    return [[{"navigable": True} for _ in range(5)] for _ in range(5)]


def test_shortest_path_and_endpoints():
    grid = fixture_grid()
    path = astar(grid, (0, 0), (4, 4), lambda _a, _b, length: length)
    assert path[0] == (0, 0) and path[-1] == (4, 4)
    assert sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])) == pytest.approx(4 * 2**0.5)


def test_blocked_cells_and_no_corner_cutting():
    grid = fixture_grid()
    grid[2][2]["navigable"] = False
    path = astar(grid, (0, 0), (4, 4), lambda _a, _b, length: length)
    assert (2, 2) not in path
    tiny = [[{"navigable": True}, {"navigable": False}], [{"navigable": False}, {"navigable": True}]]
    with pytest.raises(RouteError, match="No navigable path"):
        astar(tiny, (0, 0), (1, 1), lambda _a, _b, length: length)


def test_invalid_endpoints_and_no_path():
    grid = fixture_grid()
    with pytest.raises(RouteError) as error:
        astar(grid, (-1, 0), (4, 4), lambda _a, _b, length: length)
    assert error.value.code == "INVALID_START"
    grid[4][4]["navigable"] = False
    with pytest.raises(RouteError) as error:
        astar(grid, (0, 0), (4, 4), lambda _a, _b, length: length)
    assert error.value.code == "BLOCKED_DESTINATION"
    for cell in grid[2]:
        cell["navigable"] = False
    grid[4][4]["navigable"] = True
    with pytest.raises(RouteError) as error:
        astar(grid, (0, 0), (4, 4), lambda _a, _b, length: length)
    assert error.value.code == "NO_PATH"


def test_demo_route_tradeoff_and_statistics():
    environment = load_demo_environment()
    config = RiskConfig()
    grid = build_risk_map(environment, config)
    result = calculate_routes(grid, environment, (19, 3), (4, 32), config)
    shortest = result["shortest_route"]
    lower = result["lower_risk_route"]
    assert shortest["coordinates"][0] == lower["coordinates"][0] == {"row": 19, "col": 3}
    assert shortest["coordinates"][-1] == lower["coordinates"][-1] == {"row": 4, "col": 32}
    assert shortest["coordinates"] != lower["coordinates"]
    assert lower["distance_m"] > shortest["distance_m"]
    assert lower["average_risk"] < shortest["average_risk"]
    assert lower["accumulated_risk"] < shortest["accumulated_risk"]
    assert shortest["minimum_depth_m"] >= config.minimum_operational_depth_m
    assert all(grid[p["row"]][p["col"]]["navigable"] for p in lower["coordinates"])
    assert shortest["distance_m"] == pytest.approx(1760.66, abs=0.02)
    assert lower["distance_m"] == pytest.approx(1819.24, abs=0.02)
    assert "average modeled risk changes from" in result["comparison"]["explanation"]


def test_zero_aggressiveness_selects_shortest_geometry():
    environment = load_demo_environment()
    config = RiskConfig(routing_risk_aggressiveness=0)
    result = calculate_routes(build_risk_map(environment, config), environment, (19, 3), (4, 32), config)
    assert result["shortest_route"]["coordinates"] == result["lower_risk_route"]["coordinates"]
