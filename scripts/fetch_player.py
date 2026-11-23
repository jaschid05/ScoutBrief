"""Step 1: fetch and print raw cbbdata data for one player.

Usage (from the project root):
    python -m scripts.fetch_player --player "Cooper Flagg" --team "Duke" --year 2026
"""

import argparse
import difflib
import sys

import pandas as pd

from data import cbbdata_client as cbd


def resolve_player(roster: pd.DataFrame, name: str) -> str:
    """Match a typed name to the exact spelling in the team's roster."""
    if "player" not in roster.columns:
        raise cbd.DataSourceError(
            f"Season data has no 'player' column. Columns: {list(roster.columns)}"
        )
    names = roster["player"].dropna().unique().tolist()
    by_lower = {n.lower(): n for n in names}
    if name.lower() in by_lower:
        return by_lower[name.lower()]
    close = difflib.get_close_matches(name.lower(), list(by_lower), n=1, cutoff=0.6)
    if close:
        return by_lower[close[0]]
    raise cbd.PlayerNotFound(
        f"No player matching '{name}' on this roster. Players found: {', '.join(sorted(names))}"
    )


def show(title: str, df: pd.DataFrame, rows: int = 5) -> None:
    print(f"\n=== {title}: {len(df)} rows, {len(df.columns)} columns ===")
    if df.empty:
        print("(no data)")
        return
    print("columns:", list(df.columns))
    print("dtypes:\n" + df.dtypes.to_string())
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.head(rows).to_string())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--player", required=True)
    parser.add_argument("--team", required=True, help="Barttorvik team name, e.g. 'Duke'")
    parser.add_argument("--year", type=int, default=2026)
    args = parser.parse_args()

    try:
        roster = cbd.player_season(year=args.year, team=args.team)
        if roster.empty:
            raise cbd.PlayerNotFound(
                f"No {args.year} season data for team '{args.team}'. "
                "Check the spelling Barttorvik uses (e.g. 'Connecticut', 'St. John's')."
            )
        name = resolve_player(roster, args.player)
        print(f"Resolved '{args.player}' -> '{name}' ({args.team}, {args.year})")

        show("Season (this player)", roster[roster["player"] == name])
        show("Season (all years)", cbd.player_season(player=name, team=args.team))
        show("Game log", cbd.player_games(year=args.year, team=args.team, player=name), rows=10)
        for split in cbd.SPLIT_TYPES:
            show(f"Splits by {split}",
                 cbd.player_splits(split, year=args.year, team=args.team, player=name))
    except cbd.CbbdataError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
