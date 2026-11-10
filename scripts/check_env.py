"""
Sanity check that the PokeBot environment is set up correctly.

Run from the repo root with the venv active:
    python scripts/check_env.py
"""

import sys
from importlib.metadata import version

import numpy as np
import poke_env  #only imported to check that it loads
import torch

#We really are just looking for 3.10+
print(f"Python:   {sys.version.split()[0]}")

#Read from the installed package metadata, which works even without a __version__
print(f"poke-env: {version('poke-env')}")
print(f"torch:    {torch.__version__}")
print(f"numpy:    {np.__version__}")

#CPU-only is fine for the demo
if torch.cuda.is_available():
    print(f"GPU:      yes ({torch.cuda.get_device_name(0)})")
else:
    print("GPU:      no (running on CPU)")

#A tiny tensor op on the GPU (if there is one) proves torch actually works there
device = "cuda" if torch.cuda.is_available() else "cpu"
x = torch.rand(2, 3, device=device)
print(f"Random tensor (on {x.device}):")
print(x)
print(f"Sum of tensor: {x.sum().item():.4f}")
