"""
Battle encoder: turns a poke-env battle into a fixed-length feature vector.

Layout of the vector from encode_battle (142 floats):

    Section    Size      Contents
    our_team   6 x 10    Our 6 Pokémon, in team order
    opp_team   6 x 10    The opponent's Pokémon, in the order they were revealed
    moves      4 x 3     Our active Pokémon's 4 moves
    weather    9         One-hot over poke-env's Weather enum
    turn       1         Current turn number (not scaled)

Each Pokémon takes 10 slots:

    0      HP fraction (0.0 to 1.0)
    1      fainted (1 or 0)
    2      active, i.e. on the field (1 or 0)
    3-8    status one-hot: BRN, FRZ, PAR, PSN, SLP, TOX (all 0 = no status)
    9      revealed (1 or 0)

Our own Pokémon always have revealed = 1. Opponent Pokémon we haven't seen are
all zeros including revealed = 0, which is how the network tells "unknown"
apart from a real Pokémon.

Each move takes 3 slots:

    0      base power / 100
    1      type index (poke-env's PokemonType value: BUG = 1 ... STELLAR = 20)
    2      PP fraction (current PP / max PP)

Move order comes from slots.move_slots, so move feature i always describes
action i. Empty move slots are all zeros (type index 0 = no move), and the
weather section is all zeros when there's no weather.
"""

import numpy as np
from poke_env.battle import AbstractBattle, Move, Pokemon, Status, Weather

from pokebot.slots import NUM_MOVE_SLOTS, move_slots

#Constants
#FNT is left out since fainting has its own flag
STATUSES = [Status.BRN, Status.FRZ, Status.PAR, Status.PSN, Status.SLP, Status.TOX]
WEATHERS = list(Weather)

TEAM_SIZE = 6
NUM_MOVES = NUM_MOVE_SLOTS
POKEMON_FEATURES = 3 + len(STATUSES) + 1  #hp, fainted, active, statuses, revealed
MOVE_FEATURES = 3  #base power, type index, PP fraction

#Section sizes in vector order. The slices are built from this, so changing a
#size here shifts everything after it automatically
_SECTION_SIZES = [
    ("our_team", TEAM_SIZE * POKEMON_FEATURES),
    ("opp_team", TEAM_SIZE * POKEMON_FEATURES),
    ("moves", NUM_MOVES * MOVE_FEATURES),
    ("weather", len(WEATHERS)),
    ("turn", 1),
]

#Slices
SLICES = {}
_start = 0
for _name, _size in _SECTION_SIZES:
    SLICES[_name] = slice(_start, _start + _size)
    _start += _size

FEATURE_SIZE = _start  #142


#Encoders
def _encode_pokemon(pokemon: Pokemon) -> list[float]:
    """Encode one Pokémon we've seen as POKEMON_FEATURES floats."""
    features = [
        pokemon.current_hp_fraction,
        float(pokemon.fainted),
        float(pokemon.active),
    ]
    features += [float(pokemon.status == status) for status in STATUSES]
    features.append(1.0)  #revealed, since this is only called for Pokémon we've seen
    return features


def _encode_team(team: dict[str, Pokemon]) -> np.ndarray:
    """Encode up to 6 Pokémon. Unrevealed slots stay all zeros."""
    out = np.zeros((TEAM_SIZE, POKEMON_FEATURES), dtype=np.float32)
    for i, pokemon in enumerate(list(team.values())[:TEAM_SIZE]):
        out[i] = _encode_pokemon(pokemon)
    return out.flatten()


def _encode_moves(moves: list[Move | None]) -> np.ndarray:
    """Encode the 4 move slots from move_slots. Empty slots stay zeros."""
    out = np.zeros((NUM_MOVES, MOVE_FEATURES), dtype=np.float32)
    for i, move in enumerate(moves):
        if move is None:
            continue
        pp_fraction = move.current_pp / move.max_pp if move.max_pp else 0.0
        out[i] = [move.base_power / 100, move.type.value, pp_fraction]
    return out.flatten()


def _encode_weather(battle: AbstractBattle) -> np.ndarray:
    """One-hot of the current weather, all zeros if there is none."""
    out = np.zeros(len(WEATHERS), dtype=np.float32)
    #battle.weather maps each active weather to the turn it started
    for weather in battle.weather:
        out[WEATHERS.index(weather)] = 1.0
    return out


#Battle Encoding
def encode_battle(battle: AbstractBattle) -> tuple[np.ndarray, dict[str, slice]]:
    """
    Encode *battle* as a fixed-length vector (layout in the module docstring).

    Returns
    -------
    vector : np.ndarray
        float32 array of length FEATURE_SIZE.
    slices : dict
        Section name -> slice, so vector[slices["moves"]] gives just the move features.
    """
    vector = np.concatenate([
        _encode_team(battle.team),
        _encode_team(battle.opponent_team),
        _encode_moves(move_slots(battle)),
        _encode_weather(battle),
        np.array([battle.turn], dtype=np.float32),
    ])
    assert vector.shape == (FEATURE_SIZE,)
    return vector, SLICES
