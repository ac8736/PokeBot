"""
PokeBotPlayer: a poke-env player driven by the policy/value network.

Each turn it encodes the battle, builds the legal action mask, lets the network
pick an action, and sends the matching order to Showdown.
"""

import time

import torch
from poke_env.battle import AbstractBattle
from poke_env.player import BattleOrder, DefaultBattleOrder, Player

from pokebot.actions import action_name, action_to_order, legal_action_mask
from pokebot.features import FEATURE_SIZE, encode_battle
from pokebot.model import PolicyValueNet, act

#Constants
TOP_K = 3  #how many of the most likely actions verbose mode prints


#Player
class PokeBotPlayer(Player):
    """
    poke-env Player that picks its moves with a PolicyValueNet.
    """

    def __init__(
        self,
        *args,
        net: PolicyValueNet | None = None,
        device: str | None = None,
        verbose: bool = False,
        greedy: bool = False,
        **kwargs,
    ):
        """
        Takes the same arguments as poke-env's Player, plus the ones below.

        Parameters
        ----------
        net : PolicyValueNet or None
            Network to play with. When None, a new one with random weights is
            created on *device*.
        device : str or None
            "cpu" or "cuda" for a new network. None picks the GPU if there is
            one. Ignored when *net* is given.
        verbose : bool
            Print a summary of every decision.
        greedy : bool
            Always pick the most likely legal action instead of sampling.
        """
        super().__init__(*args, **kwargs)
        if net is None:
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            net = PolicyValueNet(FEATURE_SIZE).to(device)
        self.net = net
        self.verbose = verbose
        self.greedy = greedy
        self.decision_times_ms: list[float] = []  #one entry per decision

    def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        """Encode *battle*, let the network pick a legal action, and return its order."""
        start = time.perf_counter()

        obs, _ = encode_battle(battle)
        mask = legal_action_mask(battle)
        action, probs, value = act(self.net, obs, mask, greedy=self.greedy)
        order = action_to_order(self, battle, action)

        elapsed_ms = (time.perf_counter() - start) * 1000
        self.decision_times_ms.append(elapsed_ms)

        if self.verbose:
            self._print_decision(battle, obs, mask, action, probs, value, order, elapsed_ms)
        return order

    def _print_decision(self, battle, obs, mask, action, probs, value, order, elapsed_ms):
        """Print one decision for verbose mode."""
        print(f"--- Turn {battle.turn} ---")
        print(f"State vector: shape {obs.shape}")
        print(f"Legal mask:   {mask.astype(int).tolist()}")

        #Illegal actions have probability 0, so they're skipped
        print("Top actions:")
        for a in probs.argsort()[::-1][:TOP_K]:
            if probs[a] > 0:
                print(f"  {a:2d}  {probs[a]:6.1%}  {action_name(battle, a)}")

        print(f"Value:        {value:+.3f}")
        if isinstance(order, DefaultBattleOrder):
            #Struggle, Recharge, or nothing legal, so Showdown picks (see actions.py)
            print("Chosen:       Showdown default choice (fallback)")
        else:
            how = "(greedy: top action)" if self.greedy else "(sampled)"
            print(f"Chosen:       {action}  {probs[action]:6.1%}  {action_name(battle, action)}  {how}")
        print(f"Decision:     {elapsed_ms:.1f} ms")
