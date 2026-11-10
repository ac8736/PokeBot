"""
Policy/value network for PokeBot.

The full project trains this with behavior cloning and then PPO. In the demo
the weights stay random (PyTorch's default init), so the agent's choices are
basically random among legal actions.

    obs (input_dim) -> Linear 512 -> ReLU -> Linear 256 -> ReLU
                         |-> policy head: Linear 13 (one logit per action)
                         |-> value head:  Linear 1 -> tanh (-1 = losing, +1 = winning)
"""

import numpy as np
import torch
from torch import nn

from pokebot.actions import NUM_ACTIONS


#Network
class PolicyValueNet(nn.Module):
    """
    MLP with a shared body and two heads: 13 action logits and a value in [-1, 1].
    """

    def __init__(self, input_dim: int):
        super().__init__()
        #Shared layers both heads read from
        self.body = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        self.policy_head = nn.Linear(256, NUM_ACTIONS)
        self.value_head = nn.Linear(256, 1)

    def forward(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Return (logits, value) for a batch of observations.

        *obs* is (batch, input_dim). Logits come out as (batch, 13) and value as
        (batch,), squashed into [-1, 1] by tanh.
        """
        hidden = self.body(obs)
        logits = self.policy_head(hidden)
        value = torch.tanh(self.value_head(hidden)).squeeze(-1)
        return logits, value


#Acting
@torch.no_grad()  #acting only, no training, so skip gradient tracking
def act(
    net: PolicyValueNet, obs: np.ndarray, mask: np.ndarray, greedy: bool = False
) -> tuple[int, np.ndarray, float]:
    """
    Pick an action for one observation.

    Illegal actions get a logit of -inf, so softmax gives them probability 0 and
    they can never be chosen. Samples from the probabilities by default; with
    *greedy* it always takes the most likely legal action.

    Returns
    -------
    action : int
        The chosen action number (0-12).
    probs : np.ndarray
        All 13 action probabilities.
    value : float
        The network's estimate of how good the position is, in [-1, 1].
    """
    #Inputs have to be on the same device as the network (GPU if it's there)
    device = next(net.parameters()).device
    obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
    mask_t = torch.as_tensor(mask, dtype=torch.bool, device=device)

    logits, value = net(obs_t)
    logits = logits.squeeze(0)

    #Masking everything would give NaN probabilities, so skip the mask when
    #nothing is legal. action_to_order falls back to Showdown's default then anyway
    if mask_t.any():
        logits = logits.masked_fill(~mask_t, float("-inf"))

    probs = torch.softmax(logits, dim=-1)
    if greedy:
        action = probs.argmax().item()
    else:
        action = torch.multinomial(probs, num_samples=1).item()
    return action, probs.cpu().numpy(), value.item()
