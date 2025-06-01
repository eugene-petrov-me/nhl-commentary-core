from nhlpy import NHLClient
import json
import pandas as pd
from typing import List, Dict, Any

# Initialize the NHL API client
client = NHLClient()

def get_schedule(date: str) -> List[int]:
    """
    Fetch the NHL schedule for a given date.
    
    :param date: Date in 'YYYY-MM-DD' format.
    :return: List of game IDs for the given date.
    """
    schedule = client.schedule.get_schedule(date=date)
    return [game.get("id") for game in schedule.get("games", [])]