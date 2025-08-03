from data_fetch.schedule import get_schedule
from engine.process_game import process_game_events
from models import GameSchedule
import os
import json

DATE = "2025-04-01"  # or today's date if you're sure games exist

def main():
    output_dir = "data/events"
    os.makedirs(output_dir, exist_ok=True)

    schedule = get_schedule(DATE)

    for game in schedule:
        print(f"Processing Game ID: {game.game_id} ({game.home_team} vs {game.away_team})")
        try:
            events = process_game_events(game.game_id)
            if events:
                with open(f"{output_dir}/{game.game_id}.jsonl", "w") as f:
                    for event in events:
                        json.dump(event, f)
                        f.write("\n")
                print(f"✅ Saved events for game {game.game_id}")
            else:
                print(f"⚠️ No events for game {game.game_id}")
        except Exception as e:
            print(f"❌ Failed to process game {game.game_id}: {e}")

if __name__ == "__main__":
    main()
