"""
The agent's 13-action space and how actions turn into Showdown orders.

    Action   Meaning
    0-3      use move slot i
    4-7      use move slot i and Terastallize
    8-12     switch to bench slot i (0-4)

Slots come from pokebot.slots, so action i always means the same move as move
feature i in features.py. A slot is only legal if the server lists that move in
battle.available_moves (or that Pokémon in battle.available_switches) this turn.

Forced switches (after a faint, U-turn, etc.) are handled by the mask: only
switch actions are legal, so the network can't pick a move.
"""

import numpy as np
from poke_env.battle import AbstractBattle
from poke_env.player import BattleOrder, Player

from pokebot.slots import NUM_BENCH_SLOTS, NUM_MOVE_SLOTS, bench_slots, move_slots

#Constants
NUM_ACTIONS = 2 * NUM_MOVE_SLOTS + NUM_BENCH_SLOTS  #13

MOVE_START = 0                              #actions 0-3
TERA_START = MOVE_START + NUM_MOVE_SLOTS    #actions 4-7
SWITCH_START = TERA_START + NUM_MOVE_SLOTS  #actions 8-12


#Legal Actions
def legal_action_mask(battle: AbstractBattle) -> np.ndarray:
    """Return 13 bools, True where the action is legal this turn."""
    mask = np.zeros(NUM_ACTIONS, dtype=bool)

    #available_moves should already be empty during a forced switch, but
    #checking force_switch makes it explicit
    if not battle.force_switch:
        #Compare by move id since the server's usable-move list can hold fresh
        #Move objects, so object identity isn't reliable
        available_ids = {move.id for move in battle.available_moves}
        for i, move in enumerate(move_slots(battle)):
            if move is not None and move.id in available_ids:
                mask[MOVE_START + i] = True
                if battle.can_tera:
                    mask[TERA_START + i] = True

    for i, pokemon in enumerate(bench_slots(battle)):
        if pokemon is not None and pokemon in battle.available_switches:
            mask[SWITCH_START + i] = True

    return mask


def action_name(battle: AbstractBattle, action: int) -> str:
    """
    Readable name for *action*, e.g. "Earthquake", "Earthquake + Tera" or
    "Switch -> Garchomp". Empty slots show as "(empty move slot)".
    """
    if action < SWITCH_START:
        move = move_slots(battle)[action % NUM_MOVE_SLOTS]
        if move is None:
            return "(empty move slot)"
        name = move.entry["name"]
        return f"{name} + Tera" if action >= TERA_START else name

    pokemon = bench_slots(battle)[action - SWITCH_START]
    if pokemon is None:
        return "(empty bench slot)"
    return f"Switch -> {pokemon.name}"


#Orders
def action_to_order(player: Player, battle: AbstractBattle, action: int) -> BattleOrder:
    """
    Turn *action* into an order *player* can send to Showdown.

    Falls back to player.choose_default_move() on turns our 13 actions can't
    express. Otherwise raises ``ValueError`` if *action* isn't legal, instead of
    sending the server a bad order.
    """
    #Some turns offer a choice outside our 13 actions: Struggle when every move
    #is out of PP, or Recharge after Hyper Beam. Neither is in the 4 move slots,
    #and sometimes nothing is legal at all, so Showdown picks its default instead
    slot_ids = {move.id for move in move_slots(battle) if move is not None}
    off_slot_move = any(move.id not in slot_ids for move in battle.available_moves)
    mask = legal_action_mask(battle)
    if not mask.any() or off_slot_move:
        return player.choose_default_move()

    if not mask[action]:
        raise ValueError(f"Action {action} is not legal this turn.")

    if action < TERA_START:
        move = move_slots(battle)[action - MOVE_START]
        return player.create_order(move)

    if action < SWITCH_START:
        move = move_slots(battle)[action - TERA_START]
        return player.create_order(move, terastallize=True)

    pokemon = bench_slots(battle)[action - SWITCH_START]
    return player.create_order(pokemon)
