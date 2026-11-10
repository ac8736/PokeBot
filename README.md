# PokeBot

# Repository Contents

| Path                       | Description                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| `pokebot/accounts.py`      | `unique_account()`, which gives every run fresh Showdown usernames with a random suffix           |
| `pokebot/slots.py`         | Fixed move-slot and bench-slot order shared by the features and the action space                  |
| `pokebot/features.py`      | `encode_battle()`, which turns a battle into a fixed 142-float vector plus named slices           |
| `pokebot/actions.py`       | 13-action space: `legal_action_mask()`, `action_to_order()` and `action_name()`                   |
| `pokebot/model.py`         | `PolicyValueNet` (MLP 512 → 256, 13 policy logits, tanh value) and `act()`                        |
| `pokebot/player.py`        | `PokeBotPlayer`, a poke-env `Player` driven by the network, with verbose logs and decision timing |
| `scripts/run_demo.py`      | The demo: PokeBot vs one of poke-env's bots, with a summary at the end                            |
| `scripts/check_env.py`     | Checks the Python environment (package versions, GPU)                                             |
| `scripts/smoke_test.py`    | One battle between two built-in poke-env bots, to check the server works                          |
| `scripts/test_actions.py`  | Checks the action mask and action-to-order mapping over 3 battles                                 |
| `scripts/start_server.ps1` | Sets up and starts the local Showdown server (Windows PowerShell)                                 |
| `scripts/start_server.sh`  | Sets up and starts the local Showdown server (Mac/Linux)                                          |
| `teams/sample_gen9ou.txt`  | Default Gen 9 OU team                                                                             |
| `pokemon-showdown/`        | Local Showdown server, cloned by the start script on first run (not committed)                    |
| `SETUP.md`                 | Longer setup walkthrough                                                                          |
| `requirements.txt`         | Python dependencies                                                                               |

# Overview

PokeBot is a reinforcement learning agent for Pokémon Showdown's Gen 9 OU format, built on [poke-env](https://github.com/hsahovic/poke-env) and playing against a local Showdown server. The full project will train a policy/value network with behavior cloning and then PPO.

**Note:** This demo uses an **untrained network with random weights**. It runs the whole pipeline end to end (state encoding, legal action masking, network, Showdown orders), but it doesn't play well yet.

# Instructions

## Requirements

- Python 3.10+ (tested on 3.12)
- Node.js, which runs the Showdown server (tested on v22). Check with `node --version`
- Git

## Setup

Run everything from the repo root. [SETUP.md](SETUP.md) has a longer walkthrough.

1. Clone the repo and switch to the demo branch
   ```
   git clone https://github.com/ac8736/PokeBot.git
   cd PokeBot
   git checkout demo
   ```
2. (Windows only) Allow PowerShell to run local scripts. Only needed once
   ```
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```
3. Create and activate the virtual environment. Activate it again in every new terminal; your prompt should start with `(.venv)`
   1. Windows: `py -m venv .venv` then `.venv\Scripts\Activate.ps1`
   2. Mac/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install the Python packages
   ```
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Check the environment with `python scripts/check_env.py`. It should print the Python, poke-env, torch and numpy versions and whether torch can see a GPU
6. (Optional, NVIDIA GPU) `requirements.txt` installs the CPU build of torch. For the GPU build, run the line below (CUDA 13.4 build, so your driver has to support it; see [pytorch.org](https://pytorch.org/get-started/locally/) for other versions)
   ```
   python -m pip install --force-reinstall --no-deps torch==2.15.0 --index-url https://download.pytorch.org/whl/cu134
   ```

## Starting the server

Start the server in a second terminal, since it keeps running:

- Windows: `.\scripts\start_server.ps1`
- Mac/Linux: `bash scripts/start_server.sh`

The first start clones `smogon/pokemon-showdown` into `pokemon-showdown/`, runs `npm install` and creates `config/config.js`, so it takes a few minutes. Later starts go straight to the server. It's ready when it prints `Worker 1 now listening on 0.0.0.0:8000`. Battles can be watched at <http://localhost:8000>, and Ctrl+C stops the server.

## Running the demo

With the server running and the venv active:

```
python scripts/run_demo.py
```

| Flag          | Description                                                                                                 | Default                                                                         |
| ------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `--opponent`  | Bot to play against: `random`, `maxpower` (highest base power move) or `heuristic` (`SimpleHeuristicsPlayer`) | `random`                                                                        |
| `--n-battles` | Number of battles to play                                                                                   | `3`                                                                             |
| `--format`    | Showdown battle format                                                                                      | `gen9randombattle`                                                              |
| `--team`      | Showdown team file, used by **both** players                                                                | `teams/sample_gen9ou.txt` for `gen9ou`, required for other non-random formats   |
| `--verbose`   | Print every decision of the **first** battle                                                                | off                                                                             |
| `--greedy`    | Always pick the most likely legal action instead of sampling                                                | off                                                                             |
| `--device`    | Where to run the network: `auto`, `cpu` or `cuda`. `auto` uses the GPU if there is one                       | `auto`                                                                          |

Examples:

```
# Gen 9 OU, one battle, per-turn logs, network on the CPU
python scripts/run_demo.py --format gen9ou --n-battles 1 --verbose --device cpu

# Gen 9 OU vs the heuristic bot
python scripts/run_demo.py --format gen9ou --opponent heuristic --n-battles 1 --verbose

# Random battles vs the max-power bot, always taking the top action
python scripts/run_demo.py --opponent maxpower --n-battles 5 --greedy
```

# Example Output

From an actual run of `python scripts/run_demo.py --format gen9ou --n-battles 1 --verbose --device cpu` (turn 1, then the summary):

```
PokeBot vs random, 1 battle(s) of gen9ou
Team: C:\Users\Kazi\Desktop\PokeBot\teams\sample_gen9ou.txt
Network on: cpu
--- Turn 1 ---
State vector: shape (142,)
Legal mask:   [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
Top actions:
   0    9.1%  Dark Pulse
   6    8.8%  Knock Off + Tera
   8    8.4%  Switch -> Gliscor
Value:        +0.018
Chosen:       8    8.4%  Switch -> Gliscor  (sampled)
Decision:     3.9 ms
...

=== Summary ===
Wins:              0/1
Win rate:          0.0%
Average turns:     170.0
Avg ms / decision: 0.49 (175 decisions)
```

How to read it:

- Actions are numbered 0–12: 0–3 use a move, 4–7 use a move and Terastallize, 8–12 switch
- `Value` is the network's guess at who's winning, from -1 to +1. With random weights it doesn't mean anything yet
- On the GPU the first decision takes ~150 ms (one-time setup) and pulls up the average in short runs

# Tests

Start the server first. `check_env.py` is the only one that doesn't need it.

| Script                    | What it checks                                                                                                       | Command                          |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `scripts/check_env.py`    | Python, poke-env, torch and numpy versions, whether torch sees a GPU, and that a small tensor op works               | `python scripts/check_env.py`    |
| `scripts/smoke_test.py`   | The server and poke-env work: one `gen9randombattle` between `RandomPlayer` and `MaxBasePowerPlayer`, prints the winner and turn count | `python scripts/smoke_test.py`   |
| `scripts/test_actions.py` | Action mask and action-to-order mapping: 3 battles of random legal actions, every order checked, fails if Showdown rejects one | `python scripts/test_actions.py` |

`test_actions.py` ends with `All chosen actions mapped to legal orders.` when it passes.

# Teams

- **Default team:** `--format gen9ou` uses `teams/sample_gen9ou.txt` (Gliscor, Darkrai, Dragonite, Gholdengo, Ting-Lu, Zamazenta) for both players
- **Your own team:** export it from the Showdown teambuilder, save it as a text file and pass `--team path/to/team.txt`. Both players use it. `Gender: M` lines are fine; the demo converts them for poke-env
- **Rejected teams:** if the server rejects the team (illegal move, banned Pokémon, etc.), the demo stops with `Error: the server rejected the team.` followed by the server's reasons, and exits with code 1

# Troubleshooting

| Problem                                                                                  | Fix                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A script prints `ConnectionRefusedError` (`[WinError 1225]` on Windows) and then hangs   | The server isn't running. Ctrl+C, start it in another terminal, wait for `Worker 1 now listening on 0.0.0.0:8000` and try again                                       |
| The server crashes with `EADDRINUSE ... 8000`                                            | Another server already has port 8000, often one still open in another terminal. Use that one or stop it first                                                         |
| PowerShell says "running scripts is disabled on this system"                             | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then open a new terminal                                                                              |
| `python` opens the Microsoft Store or says "Python was not found" (Windows)              | Create the venv with `py -m venv .venv`. Once the venv is active, `python` works                                                                                      |
| `pip install` fails with `No such file or directory ... torch\include\...` and a Long Path hint | The repo's folder path is too long for torch's files. Clone it somewhere shorter (e.g. `C:\Users\<you>\PokeBot`) or enable Windows long paths                   |
| `check_env.py` says `GPU: no` on an NVIDIA machine                                       | That's the CPU build of torch. See setup step 6                                                                                                                       |
| `--device cuda` gives "torch can't see a GPU"                                            | Same as above, or there's no NVIDIA GPU. Use `--device cpu` or `auto`                                                                                                 |
| `Error: the server rejected the team.`                                                   | Fix the lines in the team file that the reasons below the error point to                                                                                              |
| A battle crashed mid-run                                                                 | Just run the script again. Every run logs in with new usernames (e.g. `PokeBot-a83b`), so a leftover battle can't block it. The old battle stays open on the server until it restarts |

# Specs

The demo runs were done on a Windows 11 Pro desktop with an Intel Core i7-14700K CPU, 32 GB of RAM and an RTX 4070 GPU.

# Team

Kazi Mansha and Andy Chen
