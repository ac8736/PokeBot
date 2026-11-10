# Setup

PokeBot needs a Python virtual environment for the agent and a local Pokémon Showdown server for it to battle on. The [README](README.md) has the short version; this goes through each step.

# Requirements

- **Python 3.10+**
- **Node.js**, since the Showdown server is a Node.js app. Install it from [nodejs.org](https://nodejs.org) and check it with `node --version`
- **Git**, which the server script uses to clone the server

# Windows (PowerShell)

Run these from the repo root.

1. Allow PowerShell to run local scripts. Windows blocks `.ps1` files by default, including the venv's activate script and `start_server.ps1`. Only needed once
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```
2. Create and activate the virtual environment. Your prompt should start with `(.venv)` after
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   1. Use `py`, not `python`, for this step. On a lot of Windows machines `python` is a Microsoft Store shortcut until a venv is active
3. Install the requirements
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Check the environment. It should print the installed versions and whether torch can see a GPU
   ```powershell
   python scripts/check_env.py
   ```
5. Start the server in a second terminal, since it keeps running
   ```powershell
   .\scripts\start_server.ps1
   ```

# Mac/Linux

Run these from the repo root.

1. Create and activate the virtual environment. Your prompt should start with `(.venv)` after
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install the requirements
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Check the environment. It should print the installed versions and whether torch can see a GPU
   ```bash
   python scripts/check_env.py
   ```
4. Start the server in a second terminal, since it keeps running
   ```bash
   bash scripts/start_server.sh
   ```

# About the server

Both server scripts do the same thing, and they work from any directory:

1. Clone [smogon/pokemon-showdown](https://github.com/smogon/pokemon-showdown) into `pokemon-showdown/` at the repo root (git-ignored), if it isn't there yet
2. Run `npm install` if `node_modules` is missing
3. Copy `config/config-example.js` to `config/config.js` if it doesn't exist
4. Start the server with `node pokemon-showdown start --no-security 8000`

`--no-security` turns off login and rate limits so local bots can battle freely, so only use it on a local server. The server is ready when it prints `Worker 1 now listening on 0.0.0.0:8000`. Battles can be watched at <http://localhost:8000>, and Ctrl+C stops the server.
