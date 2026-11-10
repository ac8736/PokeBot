#Sets up and starts a local Pokémon Showdown server for PokeBot (Windows PowerShell).
#Needs Node.js (https://nodejs.org) and git. Works from any directory:
#    .\scripts\start_server.ps1

$ErrorActionPreference = "Stop"  #stop at the first command that fails

#Paths
#The server lives in pokemon-showdown\ at the repo root (git-ignored).
#$PSScriptRoot is this script's folder, so this works from any directory
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ServerDir = Join-Path $RepoRoot "pokemon-showdown"

#Fail early with a clear message, since the server is a Node.js app
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed. Install from https://nodejs.org and try again."
}

#1. Clone the official Showdown server (first run only)
if (-not (Test-Path $ServerDir)) {
    git clone https://github.com/smogon/pokemon-showdown.git $ServerDir
    if ($LASTEXITCODE -ne 0) { Write-Error "git clone failed." }
}

Set-Location $ServerDir

#2. Install the server's Node dependencies (first run only)
if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed." }
}

#3. Create the server config from the example (first run only)
if (-not (Test-Path "config\config.js")) {
    Copy-Item "config\config-example.js" "config\config.js"
}

#4. Start the server locally on port 8000. --no-security turns off login and
#rate limits so local bots can battle freely
node pokemon-showdown start --no-security 8000
