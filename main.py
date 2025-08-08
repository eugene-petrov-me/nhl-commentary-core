from data_fetch.schedule import get_schedule
from engine.process_game import process_game_events
from engine.generate_summary import generate_summary
from models import GameSchedule
import os
import json

DATE = "2025-04-01"  # Fallback date if user input is empty

def main():
    output_dir = "data/events"
    os.makedirs(output_dir, exist_ok=True)

    date = input("Enter game date (YYYY-MM-DD): ").strip() or DATE
    schedule = get_schedule(date)

    if not schedule:
        print("No games scheduled for this date.")
        return

    print("Available games:")
    for idx, game in enumerate(schedule, start=1):
        print(f"{idx}. {game.away_team} at {game.home_team} (ID: {game.game_id})")

    selection = input("Select a game number: ").strip()
    try:
        game = schedule[int(selection) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    print(f"Processing Game ID: {game.game_id} ({game.home_team} vs {game.away_team})")
    try:
        events = process_game_events(game.game_id)
        if events:
            with open(f"{output_dir}/{game.game_id}.jsonl", "w") as f:
                for event in events:
                    json.dump(event, f)
                    f.write("\n")
            print(f"✅ Saved events for game {game.game_id}")

            summary = generate_summary(events)
            print(summary)

        else:
            print(f"⚠️ No events for game {game.game_id}")
    except Exception as e:
        print(f"❌ Failed to process game {game.game_id}: {e}")

if __name__ == "__main__":
    main()
