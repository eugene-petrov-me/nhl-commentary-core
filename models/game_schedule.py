from dataclasses import dataclass
from typing import Optional

@dataclass
class GameSchedule:
    """
    Data structure representing a single NHL game's metadata.
    """
    game_id: int
    season_id: int
    game_type: int
    home_team: str
    home_team_score: Optional[int]
    away_team: str
    away_team_score: Optional[int]
    winning_goal_scorer_id: Optional[int]
