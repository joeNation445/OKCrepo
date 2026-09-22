from __future__ import annotations

"""Helpers for the lineup summary API."""

import json
from pathlib import Path
from typing import Any

SAMPLE_SUMMARY_DATA_PATH = Path(__file__).resolve().parent / 'sample_summary_data' / 'sample_summary_data.json'
LineupRecord = dict[str, Any]


def _normalize_lineup_size(lineup_size: Any) -> int:
    try:
        normalized_lineup_size = int(lineup_size)
    except (TypeError, ValueError):
        return 5

    return max(1, min(5, normalized_lineup_size))


def _load_sample_lineups() -> list[LineupRecord]:
    with open(SAMPLE_SUMMARY_DATA_PATH) as sample_summary_data_file:
        return json.load(sample_summary_data_file)


def _truncate_sample_lineup(lineup: LineupRecord, lineup_size: int) -> LineupRecord:
    truncated_lineup = dict(lineup)
    truncated_lineup['player_ids'] = lineup['player_ids'][:lineup_size]
    truncated_lineup['players'] = lineup['players'][:lineup_size]
    return truncated_lineup


def _get_sample_lineups(lineup_size: int = 5) -> list[LineupRecord]:
    normalized_lineup_size = _normalize_lineup_size(lineup_size)
    return [
        _truncate_sample_lineup(lineup, normalized_lineup_size)
        for lineup in _load_sample_lineups()
    ]


def get_lineup_league_summary_stats(lineup_size: int = 5) -> list[LineupRecord]:
    """Return lineup summaries across the entire league."""
    
    return _get_sample_lineups(lineup_size=lineup_size)

# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import combinations
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.dbmodels.models import Player, Possession


def _safe_divide(numerator: float, denominator: float, multiplier: float = 1.0, round_digits: int = 4) -> float:
    """Safe division returning 0.0 when denominator is zero."""
    if not denominator:
        return 0.0
    return round((numerator / denominator) * multiplier, round_digits)


def get_lineup_league_summary_stats(
    lineup_size: int = 5,
    min_possessions: int = 0,
    team_id: Optional[str] = None,
    player_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Aggregates possession stats across n-man lineups for both offense and defense.
    """
    # 1. Preload all players for quick lookup
    player_lookup = {
        str(p.id): p.name
        for p in Player.objects.all().only('id', 'name')
    }

    # 2. Base possession accumulator structure
    def init_lineup_stats():
        return {
            # Offensive Base Counts
            'offensive_possessions': 0,
            'offensive_points': 0,
            'offensive_shot_attempts': 0,
            'offensive_fg2_made': 0,
            'offensive_fg2_attempted': 0,
            'offensive_fg3_made': 0,
            'offensive_fg3_attempted': 0,
            'offensive_fg_made': 0,
            'offensive_fg_attempted': 0,
            'offensive_ft_made': 0,
            'offensive_ft_attempted': 0,
            'offensive_rebounds_offense': 0,
            'offensive_rebounds_defense': 0,
            'offensive_rebound_opportunities': 0,
            'offensive_assists': 0,
            'offensive_steals': 0,
            'offensive_turnovers': 0,
            'offensive_blocks': 0,
            'offensive_offensive_fouls': 0,
            'offensive_defensive_fouls': 0,
            'offensive_shooting_fouls': 0,
            'offensive_shot_attempt_points': 0,
            'offensive_ft_potential_points': 0,
            'offensive_transition_take_fouls': 0,
            # Defensive Base Counts
            'defensive_possessions': 0,
            'defensive_points': 0,
            'defensive_shot_attempts': 0,
            'defensive_fg2_made': 0,
            'defensive_fg2_attempted': 0,
            'defensive_fg3_made': 0,
            'defensive_fg3_attempted': 0,
            'defensive_fg_made': 0,
            'defensive_fg_attempted': 0,
            'defensive_ft_made': 0,
            'defensive_ft_attempted': 0,
            'defensive_rebounds_offense': 0,
            'defensive_rebounds_defense': 0,
            'defensive_rebound_opportunities': 0,
            'defensive_assists': 0,
            'defensive_steals': 0,
            'defensive_turnovers': 0,
            'defensive_blocks': 0,
            'defensive_offensive_fouls': 0,
            'defensive_defensive_fouls': 0,
            'defensive_shooting_fouls': 0,
            'defensive_shot_attempt_points': 0,
            'defensive_ft_potential_points': 0,
            'defensive_transition_take_fouls': 0,
            'seconds': 0.0,
        }

    # lineup_map: (team_id_str, tuple_of_sorted_player_id_strs) -> stats_dict
    lineup_map: Dict[Tuple[str, Tuple[str, ...]], Dict[str, Any]] = defaultdict(init_lineup_stats)

    # 3. Stream possessions from DB
    possessions_qs = Possession.objects.all().values(
        'offensive_team_id',
        'defensive_team_id',
        'offensive_player_ids',
        'defensive_player_ids',
        'seconds',
        'fg2_made',
        'fg2_attempted',
        'fg3_made',
        'fg3_attempted',
        'fg_made',
        'fg_attempted',
        'ft_made',
        'ft_attempted',
        'rebounds_offense',
        'rebounds_defense',
        'rebound_opportunities',
        'assists',
        'steals',
        'turnovers',
        'blocks',
        'offensive_fouls',
        'defensive_fouls',
        'shooting_fouls',
        'points',
        'shot_attempts',
        'shot_attempt_points',
        'ft_potential_points',
        'transition_take_fouls',
    )

    for row in possessions_qs.iterator(chunk_size=2000):
        # --- Offensive Side ---
        off_team_id = str(row['offensive_team_id'])
        off_players = sorted(str(pid) for pid in row['offensive_player_ids'])
        for combo in combinations(off_players, lineup_size):
            entry = lineup_map[(off_team_id, combo)]
            entry['offensive_possessions'] += 1
            entry['offensive_points'] += row['points']
            entry['offensive_shot_attempts'] += row['shot_attempts']
            entry['offensive_fg2_made'] += row['fg2_made']
            entry['offensive_fg2_attempted'] += row['fg2_attempted']
            entry['offensive_fg3_made'] += row['fg3_made']
            entry['offensive_fg3_attempted'] += row['fg3_attempted']
            entry['offensive_fg_made'] += row['fg_made']
            entry['offensive_fg_attempted'] += row['fg_attempted']
            entry['offensive_ft_made'] += row['ft_made']
            entry['offensive_ft_attempted'] += row['ft_attempted']
            entry['offensive_rebounds_offense'] += row['rebounds_offense']
            entry['offensive_rebounds_defense'] += row['rebounds_defense']
            entry['offensive_rebound_opportunities'] += row['rebound_opportunities']
            entry['offensive_assists'] += row['assists']
            entry['offensive_steals'] += row['steals']
            entry['offensive_turnovers'] += row['turnovers']
            entry['offensive_blocks'] += row['blocks']
            entry['offensive_offensive_fouls'] += row['offensive_fouls']
            entry['offensive_defensive_fouls'] += row['defensive_fouls']
            entry['offensive_shooting_fouls'] += row['shooting_fouls']
            entry['offensive_shot_attempt_points'] += row['shot_attempt_points']
            entry['offensive_ft_potential_points'] += row['ft_potential_points']
            entry['offensive_transition_take_fouls'] += row['transition_take_fouls']
            entry['seconds'] += row['seconds']

        # --- Defensive Side ---
        def_team_id = str(row['defensive_team_id'])
        def_players = sorted(str(pid) for pid in row['defensive_player_ids'])
        for combo in combinations(def_players, lineup_size):
            entry = lineup_map[(def_team_id, combo)]
            entry['defensive_possessions'] += 1
            entry['defensive_points'] += row['points']
            entry['defensive_shot_attempts'] += row['shot_attempts']
            entry['defensive_fg2_made'] += row['fg2_made']
            entry['defensive_fg2_attempted'] += row['fg2_attempted']
            entry['defensive_fg3_made'] += row['fg3_made']
            entry['defensive_fg3_attempted'] += row['fg3_attempted']
            entry['defensive_fg_made'] += row['fg_made']
            entry['defensive_fg_attempted'] += row['fg_attempted']
            entry['defensive_ft_made'] += row['ft_made']
            entry['defensive_ft_attempted'] += row['ft_attempted']
            entry['defensive_rebounds_offense'] += row['rebounds_offense']
            entry['defensive_rebounds_defense'] += row['rebounds_defense']
            entry['defensive_rebound_opportunities'] += row['rebound_opportunities']
            entry['defensive_assists'] += row['assists']
            entry['defensive_steals'] += row['steals']
            entry['defensive_turnovers'] += row['turnovers']
            entry['defensive_blocks'] += row['blocks']
            entry['defensive_offensive_fouls'] += row['offensive_fouls']
            entry['defensive_defensive_fouls'] += row['defensive_fouls']
            entry['defensive_shooting_fouls'] += row['shooting_fouls']
            entry['defensive_shot_attempt_points'] += row['shot_attempt_points']
            entry['defensive_ft_potential_points'] += row['ft_potential_points']
            entry['defensive_transition_take_fouls'] += row['transition_take_fouls']

    # 4. Format outputs and compute advanced analytics
    results = []
    for (t_id, player_combo), stats in lineup_map.items():
        total_poss = stats['offensive_possessions'] + stats['defensive_possessions']

        # Apply optional filters
        if total_poss < min_possessions:
            continue
        if team_id and t_id != team_id:
            continue
        if player_id and player_id not in player_combo:
            continue

        off_poss = stats['offensive_possessions']
        def_poss = stats['defensive_possessions']

        # Standard shooting percentages
        off_fg_pct = _safe_divide(stats['offensive_fg_made'], stats['offensive_fg_attempted'])
        off_fg2_pct = _safe_divide(stats['offensive_fg2_made'], stats['offensive_fg2_attempted'])
        off_fg3_pct = _safe_divide(stats['offensive_fg3_made'], stats['offensive_fg3_attempted'])

        def_fg_pct = _safe_divide(stats['defensive_fg_made'], stats['defensive_fg_attempted'])
        def_fg2_pct = _safe_divide(stats['defensive_fg2_made'], stats['defensive_fg2_attempted'])
        def_fg3_pct = _safe_divide(stats['defensive_fg3_made'], stats['defensive_fg3_attempted'])

        # Advanced NBA Analytics
        # Efficiency Ratings (per 100 possessions)
        off_rating = _safe_divide(stats['offensive_points'], off_poss, multiplier=100.0, round_digits=2)
        def_rating = _safe_divide(stats['defensive_points'], def_poss, multiplier=100.0, round_digits=2)
        net_rating = round(off_rating - def_rating, 2)
        plus_minus = stats['offensive_points'] - stats['defensive_points']

        # Effective Field Goal % (eFG%)
        off_efg_pct = _safe_divide(
            stats['offensive_fg_made'] + 0.5 * stats['offensive_fg3_made'],
            stats['offensive_fg_attempted'],
        )
        def_efg_pct = _safe_divide(
            stats['defensive_fg_made'] + 0.5 * stats['defensive_fg3_made'],
            stats['defensive_fg_attempted'],
        )

        # True Shooting % (TS%)
        off_ts_denom = 2 * (stats['offensive_fg_attempted'] + 0.44 * stats['offensive_ft_attempted'])
        off_ts_pct = _safe_divide(stats['offensive_points'], off_ts_denom)

        def_ts_denom = 2 * (stats['defensive_fg_attempted'] + 0.44 * stats['defensive_ft_attempted'])
        def_ts_pct = _safe_divide(stats['defensive_points'], def_ts_denom)

        # Rebounding rates
        oreb_pct = _safe_divide(
            stats['offensive_rebounds_offense'],
            stats['offensive_rebound_opportunities'],
        )
        dreb_pct = _safe_divide(
            stats['defensive_rebounds_defense'],
            stats['defensive_rebound_opportunities'],
        )

        # Ball control
        tov_pct = _safe_divide(stats['offensive_turnovers'], off_poss, multiplier=100.0, round_digits=2)
        ast_pct = _safe_divide(stats['offensive_assists'], stats['offensive_fg_made'], multiplier=100.0, round_digits=2)

        players_list = [
            {'player_id': pid, 'name': player_lookup.get(pid, 'Unknown')}
            for pid in player_combo
        ]

        # Preserve exact field compatibility with sample_summary_data.json
        row_dict = {
            **stats,
            'total_possessions': total_poss,
            'offensive_fg_pct': off_fg_pct,
            'offensive_fg2_pct': off_fg2_pct,
            'offensive_fg3_pct': off_fg3_pct,
            'defensive_fg_pct': def_fg_pct,
            'defensive_fg2_pct': def_fg2_pct,
            'defensive_fg3_pct': def_fg3_pct,
            'team_id': t_id,
            'player_ids': list(player_combo),
            'players': players_list,
            # Enhanced Coach/Executive Metrics
            'offensive_rating': off_rating,
            'defensive_rating': def_rating,
            'net_rating': net_rating,
            'plus_minus': plus_minus,
            'offensive_efg_pct': off_efg_pct,
            'defensive_efg_pct': def_efg_pct,
            'offensive_ts_pct': off_ts_pct,
            'defensive_ts_pct': def_ts_pct,
            'oreb_pct': oreb_pct,
            'dreb_pct': dreb_pct,
            'turnover_pct': tov_pct,
            'assist_pct': ast_pct,
        }
        results.append(row_dict)

    # Default sort by total possessions descending
    results.sort(key=lambda x: x['total_possessions'], reverse=True)
    return results