#!/usr/bin/env bash
#Sets up and starts a local Pokémon Showdown server for PokeBot (Mac/Linux).
#Needs Node.js (https://nodejs.org) and git. Works from any directory:
#    bash scripts/start_server.sh

set -e  #stop at the first command that fails

#Paths
#The server lives in pokemon-showdown/ at the repo root (git-ignored)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_DIR="$REPO_ROOT/pokemon-showdown"

#Fail early with a clear message, since the server is a Node.js app
if ! command -v node > /dev/null; then
    echo "Error: Node.js is not installed. Install from https://nodejs.org and try again."
    exit 1
fi

#1. Clone the official Showdown server (first run only)
if [ ! -d "$SERVER_DIR" ]; then
    git clone https://github.com/smogon/pokemon-showdown.git "$SERVER_DIR"
fi

cd "$SERVER_DIR"

#2. Install the server's Node dependencies (first run only)
if [ ! -d node_modules ]; then
    npm install
fi

#3. Create the server config from the example (first run only)
if [ ! -f config/config.js ]; then
    cp config/config-example.js config/config.js
fi

#4. Start the server locally on port 8000. --no-security turns off login and
#rate limits so local bots can battle freely
node pokemon-showdown start --no-security 8000
