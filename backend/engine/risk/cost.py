"""Effective travel time, cargo penalty profiles, hard filters, and route ranking."""

from typing import List, Optional, Tuple

from engine.config import (
    LATENESS_WEIGHT,
    P_BLOCK,
    get_cargo_profile,
)
from engine.models import RouteMetrics, RouteOption


def calculate_effective_time(
    duration_min: float,
    metrics: RouteMetrics,
    cargo: str = "general",
    minutes_to_deadline: Optional[float] = None,
) -> float:
    """Calculate generalized cost in minutes ("effective time").

    Formula:
    effective_time = duration_min
                   + risk_aversion(cargo) * delay_penalty_min(cargo) * expected_disruptions
                   + lateness_weight * max(0, duration_min - minutes_to_deadline)
    """
    profile = get_cargo_profile(cargo)

    risk_penalty = profile.risk_aversion * profile.delay_penalty_min * metrics.expected_disruptions

    lateness_penalty = 0.0
    if minutes_to_deadline is not None:
        overdue_min = max(0.0, duration_min - minutes_to_deadline)
        lateness_penalty = LATENESS_WEIGHT * overdue_min

    total_effective = duration_min + risk_penalty + lateness_penalty
    return round(float(total_effective), 1)


def rank_and_explain_routes(
    routes: List[RouteOption],
    cargo: str = "general",
    p_block_threshold: float = P_BLOCK,
) -> Tuple[List[RouteOption], Optional[RouteOption]]:
    """Apply hard filters (closures, max_p >= P_BLOCK), rank by effective_time, and generate reasons.

    Returns:
    (ranked_routes_list, recommended_route)
    """
    if not routes:
        return [], None

    # 1. Apply hard filters
    for r in routes:
        has_closure = r.metrics.closed_segments > 0
        exceeds_p_block = r.metrics.max_p >= p_block_threshold
        r.is_hard_filtered = has_closure or exceeds_p_block

    valid_routes = [r for r in routes if not r.is_hard_filtered]

    if valid_routes:
        # Sort valid routes by effective_time, breaking ties by max_p
        sorted_valid = sorted(valid_routes, key=lambda x: (x.effective_time, x.metrics.max_p))
        recommended = sorted_valid[0]
        recommended.is_recommended = True

        # Generate reasons for recommended route compared to others
        fastest_route = min(routes, key=lambda x: x.duration_min)
        if recommended.route_id != fastest_route.route_id:
            time_diff = round(recommended.duration_min - fastest_route.duration_min, 1)
            high_cell_diff = fastest_route.metrics.n_high_cells - recommended.metrics.n_high_cells
            reason = f"Avoids {max(0, high_cell_diff)} high-risk flood cells on {fastest_route.label} (+{time_diff} min)"
            recommended.reasons.append(reason)
        else:
            recommended.reasons.append(f"Fastest and lowest flood-risk corridor for {cargo.upper()} cargo.")

        # Hard-filtered routes go to the end
        filtered_routes = [r for r in routes if r.is_hard_filtered]
        sorted_filtered = sorted(filtered_routes, key=lambda x: (x.effective_time, x.metrics.max_p))
        all_ranked = sorted_valid + sorted_filtered
        return all_ranked, recommended

    else:
        # All routes failed hard filters: select the least bad option
        sorted_all = sorted(routes, key=lambda x: (x.metrics.closed_segments, x.metrics.max_p, x.effective_time))
        recommended = sorted_all[0]
        recommended.is_recommended = False
        recommended.reasons.append(
            f"All candidate routes exceed safety threshold (P_BLOCK={p_block_threshold}) or have closures."
        )
        return sorted_all, recommended
