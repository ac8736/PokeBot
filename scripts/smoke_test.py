"""
Smoke test: plays one battle on the local Showdown server.

Plays one gen9randombattle between poke-env's built-in RandomPlayer and
MaxBasePowerPlayer, then prints the winner and how many turns it took.

Start the server first, then in another terminal:
    python scripts/smoke_test.py
"""

import asyncio
import sys
from pathlib import Path

from poke_env import LocalhostServerConfiguration, MaxBasePowerPlayer, RandomPlayer

#Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#Lets this script import the pokebot package from the repo root
sys.path.insert(0, str(PROJECT_ROOT))

from pokebot.accounts import unique_account  # noqa: E402


#Entry Point
async def main():
    #Fresh usernames each run, so a battle left over from a crashed run can't block this one
    random_player = RandomPlayer(
        unique_account("Random"),
        battle_format="gen9randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    max_power_player = MaxBasePowerPlayer(
        unique_account("MaxPower"),
        battle_format="gen9randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    await random_player.battle_against(max_power_player, n_battles=1)

    #Each player keeps a dict of its finished battles, and there's only one
    battle = next(iter(random_player.battles.values()))

    #battle.won is from random_player's point of view (None means a tie)
    if battle.won is None:
        winner = "Tie"
    elif battle.won:
        winner = f"RandomPlayer ({random_player.username})"
    else:
        winner = f"MaxBasePowerPlayer ({max_power_player.username})"

    print(f"Winner: {winner}")
    print(f"Turns:  {battle.turn}")


if __name__ == "__main__":
    asyncio.run(main())
