"""
Fixed move and bench slot orders, shared by features.py and actions.py.

Move feature i and action i have to mean the same move (and the same for bench
slots), so both files get their slot order from here.
"""

from poke_env.battle import AbstractBattle, Move, Pokemon

#Constants
NUM_MOVE_SLOTS = 4
NUM_BENCH_SLOTS = 5


#Slot Orders
def move_slots(battle: AbstractBattle) -> list[Move | None]:
    """
    Our active Pokémon's moves in a fixed order, padded with None to 4.

    Uses the order the server sent the moveset in, so slots don't shift when a
    move is disabled or runs out of PP.
    """
    pokemon = battle.active_pokemon
    moves = list(pokemon.moves.values())[:NUM_MOVE_SLOTS] if pokemon else []
    return moves + [None] * (NUM_MOVE_SLOTS - len(moves))


def bench_slots(battle: AbstractBattle) -> list[Pokemon | None]:
    """
    Our non-active Pokémon in team order, padded with None to 5.

    Same team order features.py uses for our_team, minus the active Pokémon.
    Fainted Pokémon keep their slot but can't be switched to.
    """
    bench = [p for p in battle.team.values() if not p.active][:NUM_BENCH_SLOTS]
    return bench + [None] * (NUM_BENCH_SLOTS - len(bench))
