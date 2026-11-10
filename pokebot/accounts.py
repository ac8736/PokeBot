"""
Unique Showdown usernames for each run.

poke-env's automatic usernames are the same every run ("RandomPlayer 1",
"MaxBasePowerPlay 1", ...). If a run crashes mid-battle, the local server keeps
that battle open under those names and the next run hangs behind it, so every
run gets a short random suffix instead.
"""

import secrets

from poke_env import AccountConfiguration

#Constants
MAX_USERNAME_LENGTH = 18  #Showdown's limit
SUFFIX_LENGTH = 4         #hex characters, e.g. "a3f9"


#Accounts
def unique_account(prefix: str) -> AccountConfiguration:
    """
    Return an account named like "Random-a3f9", unique to this run.

    *prefix* is cut short if needed to fit Showdown's 18-character limit. No
    password is needed on a local server started with --no-security.
    """
    suffix = secrets.token_hex(SUFFIX_LENGTH // 2)
    prefix = prefix[: MAX_USERNAME_LENGTH - SUFFIX_LENGTH - 1]
    return AccountConfiguration(f"{prefix}-{suffix}", None)
