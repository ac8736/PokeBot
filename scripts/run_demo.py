"""
PokeBot demo: the untrained network vs one of poke-env's built-in bots.

The network's weights are random, so expect it to lose most battles. Gen 9 OU
uses teams/sample_gen9ou.txt for both players unless --team gives another
team file (Showdown export format).

Start the server first, then in another terminal:
    python scripts/run_demo.py --opponent maxpower --n-battles 3 --verbose
    python scripts/run_demo.py --format gen9ou
    python scripts/run_demo.py --format gen9ou --team path/to/team.txt
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import torch
from poke_env import (
    LocalhostServerConfiguration,
    MaxBasePowerPlayer,
    RandomPlayer,
    SimpleHeuristicsPlayer,
)

#Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#Lets this script import the pokebot package from the repo root
sys.path.insert(0, str(PROJECT_ROOT))

from pokebot.accounts import unique_account  # noqa: E402
from pokebot.player import PokeBotPlayer  # noqa: E402

#Constants
OPPONENTS = {
    "random": RandomPlayer,
    "maxpower": MaxBasePowerPlayer,
    "heuristic": SimpleHeuristicsPlayer,
}

#Team used for each format when --team isn't given
DEFAULT_TEAMS = {
    "gen9ou": PROJECT_ROOT / "teams" / "sample_gen9ou.txt",
}


#Arguments
def parse_args() -> argparse.Namespace:
    """Parse and check the command-line flags."""
    parser = argparse.ArgumentParser(description="Play PokeBot against a poke-env bot.")
    parser.add_argument("--opponent", choices=OPPONENTS, default="random",
                        help="which built-in poke-env bot to play against (default: random)")
    parser.add_argument("--n-battles", type=int, default=3,
                        help="number of battles to play (default: 3)")
    parser.add_argument("--format", default="gen9randombattle",
                        help="Showdown battle format (default: gen9randombattle)")
    parser.add_argument("--team", type=Path,
                        help="Showdown team file (default for gen9ou: teams/sample_gen9ou.txt)")
    parser.add_argument("--verbose", action="store_true",
                        help="print every decision of the first battle")
    parser.add_argument("--greedy", action="store_true",
                        help="always pick the most likely legal action instead of sampling")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto",
                        help="where to run the network; auto uses the GPU if there is one (default: auto)")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("--device cuda was given, but torch can't see a GPU. Use --device cpu or auto")

    if args.team is None:
        args.team = DEFAULT_TEAMS.get(args.format)
    #Random battle formats hand out teams, every other format needs one
    if "randombattle" not in args.format and args.team is None:
        parser.error(f"--team is required for {args.format}")
    if args.n_battles < 1:
        parser.error("--n-battles must be at least 1")
    return args


#Teams
def load_team(path: Path) -> str:
    """
    Read a team in Showdown export format from *path*.

    Some exports put gender on its own line ("Gender: M"), but poke-env only
    understands it in the name line ("Gliscor (M) @ Toxic Orb") and otherwise
    reads "Gender: M" as a Pokémon called "genderm", so it gets moved there.
    """
    pokemon_blocks = []
    #utf-8-sig also strips the invisible marker Notepad can add at the start
    for block in path.read_text(encoding="utf-8-sig").strip().split("\n\n"):
        lines = block.strip().splitlines()
        gender_lines = [line for line in lines if line.startswith("Gender: ")]
        if gender_lines:
            lines.remove(gender_lines[0])
            gender = gender_lines[0].removeprefix("Gender: ").strip()
            name, at, item = lines[0].partition(" @ ")
            lines[0] = f"{name} ({gender}){at}{item}"
        pokemon_blocks.append("\n".join(lines))
    return "\n\n".join(pokemon_blocks)


class TeamRejectedWatcher(logging.Handler):
    """
    Notices when the server rejects a team.

    The server reports it as a popup, which poke-env only logs, and the
    challenge then waits forever. Catching that log line lets the demo stop and
    show the server's reasons instead of hanging.
    """

    def __init__(self):
        super().__init__()
        self.rejected = asyncio.Event()
        self.reasons = ""
        #poke-env talks to the server on its own event loop in a background
        #thread, so emit() runs on that thread. asyncio.Event isn't thread-safe,
        #so set() gets handed back to our loop
        self.loop = asyncio.get_running_loop()

    def emit(self, record):
        message = record.getMessage()
        if "Your team was rejected" in message:
            #Showdown separates popup lines with "||"
            self.reasons = message.split("|popup|", 1)[-1].replace("||", "\n")
            self.loop.call_soon_threadsafe(self.rejected.set)


#Battles
async def play(bot, opponent, n_battles: int, watcher: TeamRejectedWatcher):
    """Play *n_battles*, exiting with an error if the server rejects the team."""
    battles = asyncio.create_task(bot.battle_against(opponent, n_battles=n_battles))
    rejected = asyncio.create_task(watcher.rejected.wait())
    await asyncio.wait({battles, rejected}, return_when=asyncio.FIRST_COMPLETED)

    if watcher.rejected.is_set():
        battles.cancel()
        print("\nError: the server rejected the team.", file=sys.stderr)
        print(watcher.reasons, file=sys.stderr)
        sys.exit(1)
    rejected.cancel()


#Entry Point
async def main():
    args = parse_args()

    #Both sides use the same team in non-random formats
    team = load_team(args.team) if args.team else None

    common = dict(
        battle_format=args.format,
        server_configuration=LocalhostServerConfiguration,
        team=team,
    )
    #Fresh usernames each run, so a battle left over from a crashed run can't block this one
    device = None if args.device == "auto" else args.device
    bot = PokeBotPlayer(unique_account("PokeBot"), device=device, greedy=args.greedy, **common)
    opponent = OPPONENTS[args.opponent](unique_account(args.opponent.capitalize()), **common)

    watcher = TeamRejectedWatcher()
    bot.logger.addHandler(watcher)
    opponent.logger.addHandler(watcher)

    print(f"PokeBot vs {args.opponent}, {args.n_battles} battle(s) of {args.format}")
    if args.team:
        print(f"Team: {args.team}")
    print(f"Network on: {next(bot.net.parameters()).device}")

    #Verbose logs (if asked for) only cover the first battle
    bot.verbose = args.verbose
    await play(bot, opponent, 1, watcher)
    bot.verbose = False
    if args.n_battles > 1:
        await play(bot, opponent, args.n_battles - 1, watcher)

    battles = list(bot.battles.values())
    wins = bot.n_won_battles
    avg_turns = sum(b.turn for b in battles) / len(battles)
    avg_ms = sum(bot.decision_times_ms) / len(bot.decision_times_ms)

    print()
    print("=== Summary ===")
    print(f"Wins:              {wins}/{len(battles)}")
    print(f"Win rate:          {wins / len(battles):.1%}")
    print(f"Average turns:     {avg_turns:.1f}")
    print(f"Avg ms / decision: {avg_ms:.2f} ({len(bot.decision_times_ms)} decisions)")


if __name__ == "__main__":
    asyncio.run(main())
