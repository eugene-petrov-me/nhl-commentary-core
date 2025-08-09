import argparse

from data_fetch.schedule import get_schedule
from engine.summarize_game import summarize_game

DATE = "2025-04-01"  # Fallback date if user input is empty

def main():
    parser = argparse.ArgumentParser(description="Summarize an NHL game")
    parser.add_argument("--ai", dest="use_ai", action="store_true", help="Use AI summary")
    parser.add_argument(
        "--rule",
        dest="use_ai",
        action="store_false",
        help="Use rule-based summary",
    )
    parser.set_defaults(use_ai=None)
    args = parser.parse_args()

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
    use_ai = args.use_ai
    if use_ai is None:
        choice = input("Use AI-generated summary? [Y/n]: ").strip().lower()
        use_ai = choice != "n"

    try:
        summary = summarize_game(game.game_id, use_ai=use_ai)
        if summary:
            print(summary)
        else:
            print(f"⚠️ No events for game {game.game_id}")
    except Exception as e:
        print(f"❌ Failed to process game {game.game_id}: {e}")

if __name__ == "__main__":
    main()
