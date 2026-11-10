"""
Test for pokebot/actions.py against the local Showdown server.

Plays 3 gen9randombattle games with a player that picks a random legal action
from legal_action_mask every turn, and checks that every chosen action turns
into a legal order. Also fails if Showdown rejects any order.

Start the server first, then in another terminal:
    python scripts/test_actions.py
"""

import asyncio
import logging
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from poke_env import LocalhostServerConfiguration, MaxBasePowerPlayer
from poke_env.player import DefaultBattleOrder, Player

#Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#Lets this script import the pokebot package from the repo root
sys.path.insert(0, str(PROJECT_ROOT))

from pokebot.accounts import unique_account  # noqa: E402
from pokebot.actions import NUM_ACTIONS, SWITCH_START, action_to_order, legal_action_mask  # noqa: E402

#Constants
NUM_BATTLES = 3


#Test Helpers
class RejectedOrderCounter(logging.Handler):
    """
    Collects Showdown's error replies.

    poke-env logs them and quietly retries, so without this a rejected order
    would go unnoticed.
    """

    def __init__(self):
        super().__init__()
        self.errors = []

    def emit(self, record):
        if "Error message received" in record.getMessage():
            self.errors.append(record.getMessage())


class RandomMaskPlayer(Player):
    """
    Picks a uniformly random legal action and checks the order it turns into.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rng = np.random.default_rng()
        self.stats = Counter()
        self.failures = []

    def choose_move(self, battle):
        #poke-env runs choose_move in a background task, where an exception just
        #stalls the battle and the script hangs instead of failing. So failures get
        #recorded, a safe default order goes out, and main() fails at the end
        try:
            return self.choose_and_check(battle)
        except Exception as e:
            self.failures.append(f"turn {battle.turn}: {type(e).__name__}: {e}")
            return self.choose_default_move()

    def choose_and_check(self, battle):
        """Pick a random legal action for *battle* and assert its order is legal."""
        mask = legal_action_mask(battle)
        assert mask.shape == (NUM_ACTIONS,)

        #The mask can't hide a legal switch, so every Pokémon the server offers
        #needs a bench slot
        assert mask[SWITCH_START:].sum() == len(battle.available_switches), (
            f"mask has {mask[SWITCH_START:].sum()} switches, "
            f"server offers {len(battle.available_switches)}"
        )

        legal = np.flatnonzero(mask)
        action = int(self.rng.choice(legal)) if len(legal) else 0
        order = action_to_order(self, battle, action)

        if isinstance(order, DefaultBattleOrder):
            #Fallback case (Struggle, Recharge, or nothing legal)
            self.stats["fallback"] += 1
            return order

        assert mask[action], f"chose illegal action {action}"
        if action < SWITCH_START:
            #A move order has to use a move the server lists as usable, and only
            #Terastallize when that's allowed
            available_ids = {move.id for move in battle.available_moves}
            assert order.order.id in available_ids, f"{order.order.id} not usable"
            assert order.terastallize == (action >= 4)
            assert battle.can_tera or not order.terastallize
            self.stats["tera" if order.terastallize else "move"] += 1
        else:
            assert order.order in battle.available_switches, "switch target not available"
            self.stats["switch"] += 1
        return order


#Entry Point
async def main():
    #Fresh usernames each run, so a battle left over from a crashed run can't block this one
    player = RandomMaskPlayer(
        unique_account("MaskTest"),
        battle_format="gen9randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    opponent = MaxBasePowerPlayer(
        unique_account("MaxPower"),
        battle_format="gen9randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    rejected = RejectedOrderCounter()
    player.logger.addHandler(rejected)

    await player.battle_against(opponent, n_battles=NUM_BATTLES)

    assert player.n_finished_battles == NUM_BATTLES
    assert not player.failures, f"Checks failed: {player.failures}"
    assert not rejected.errors, f"Showdown rejected orders: {rejected.errors}"

    print(f"Battles finished: {player.n_finished_battles}")
    print(f"Orders chosen:    {dict(player.stats)}")
    print("All chosen actions mapped to legal orders.")


if __name__ == "__main__":
    asyncio.run(main())
