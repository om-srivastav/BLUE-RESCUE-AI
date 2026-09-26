from math import hypot
from time import perf_counter

from app.services.risk.config import RiskConfig
from app.services.risk.engine import DemoEnvironment, clamp, directional_current_risk
from app.services.routing.astar import Point, astar


def movement_risk(cell: dict, first: Point, second: Point, config: RiskConfig) -> float:
    directional = directional_current_risk(cell["u_current_mps"], cell["v_current_mps"], second[0] - first[0], second[1] - first[1], config)
    return clamp(cell["total_risk"] - config.weights.current * cell["current_risk"] + config.weights.current * directional)


def route_stats(path: list[Point], grid: list[list[dict]], environment: DemoEnvironment, config: RiskConfig, route_type: str, computation_time_ms: float) -> dict:
    distance = 0.0
    exposures = []
    current_exposures = []
    for first, second in zip(path, path[1:]):
        distance += hypot(second[0] - first[0], second[1] - first[1]) * config.cell_size_m
        cell = grid[second[0]][second[1]]
        exposures.append(movement_risk(cell, first, second, config))
        current_exposures.append(directional_current_risk(cell["u_current_mps"], cell["v_current_mps"], second[0] - first[0], second[1] - first[1], config))
    if not exposures:
        exposures = [grid[path[0][0]][path[0][1]]["total_risk"]]
    depths = [grid[row][col]["depth_m"] for row, col in path]
    waves = [grid[row][col]["wave_height_m"] for row, col in path]
    approached = [hazard["id"] for hazard in environment.hazards if hazard.get("status", "ACTIVE") == "ACTIVE" and min(hypot(row - hazard["row"], col - hazard["col"]) for row, col in path) < hazard["radius_cells"]]
    return {
        "route_type": route_type, "coordinates": [{"row": row, "col": col} for row, col in path],
        "distance_m": round(distance, 2), "average_risk": round(sum(exposures) / len(exposures), 5),
        "accumulated_risk": round(sum(exposures), 5), "minimum_depth_m": min(depths),
        "hazards_approached": approached, "average_wave_height_m": round(sum(waves) / len(waves), 3),
        "accumulated_wave_exposure_m": round(sum(waves), 3), "computation_time_ms": round(computation_time_ms, 3),
        "average_directional_current_risk": round(sum(current_exposures) / len(current_exposures), 5) if current_exposures else 0.0,
        "distance_basis": "SIMULATED_50_METER_GRID_CELLS",
    }


def compare_routes(shortest: dict, lower: dict) -> dict:
    distance_delta = round(lower["distance_m"] - shortest["distance_m"], 2)
    risk_delta = round(lower["average_risk"] - shortest["average_risk"], 5)
    avoided = sorted(set(shortest["hazards_approached"]) - set(lower["hazards_approached"]))
    details = [f"Modeled distance changes by {distance_delta:+.0f} m and average modeled risk changes from {shortest['average_risk']:.3f} to {lower['average_risk']:.3f}."]
    if avoided:
        details.append("It avoids the influence radius of " + ", ".join(avoided) + ".")
    if lower["minimum_depth_m"] > shortest["minimum_depth_m"]:
        details.append("Its minimum modeled depth is greater.")
    if lower["average_wave_height_m"] < shortest["average_wave_height_m"]:
        details.append("Its mean modeled wave exposure is lower.")
    if lower["average_directional_current_risk"] < shortest["average_directional_current_risk"]:
        details.append("Its mean directional current penalty is lower.")
    if lower["coordinates"] == shortest["coordinates"]:
        details.append("Both objectives selected the same grid path under current settings.")
    return {"distance_difference_m": distance_delta, "average_risk_difference": risk_delta, "hazards_avoided": avoided, "minimum_depth_difference_m": round(lower["minimum_depth_m"] - shortest["minimum_depth_m"], 2), "explanation": " ".join(details)}


def calculate_routes(grid: list[list[dict]], environment: DemoEnvironment, start: Point, destination: Point, config: RiskConfig) -> dict:
    begin = perf_counter()
    short_path = astar(grid, start, destination, lambda _a, _b, length: length)
    shortest = route_stats(short_path, grid, environment, config, "SHORTEST", (perf_counter() - begin) * 1000)
    begin = perf_counter()
    def risk_cost(first: Point, second: Point, length: float) -> float:
        cell = grid[second[0]][second[1]]
        return length * (1 + config.routing_risk_aggressiveness * movement_risk(cell, first, second, config))
    lower_path = astar(grid, start, destination, risk_cost)
    lower = route_stats(lower_path, grid, environment, config, "LOWER_MODELED_RISK", (perf_counter() - begin) * 1000)
    return {"shortest_route": shortest, "lower_risk_route": lower, "comparison": compare_routes(shortest, lower)}
