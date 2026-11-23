"""One-time helper: log in to cbbdata and save the API key into .env.

Put CBD_USER and CBD_PW in .env (or the environment), then run from the
project root:
    python -m scripts.get_api_key

The key is written to .env as CBBDATA_API_KEY and never printed. You can
delete CBD_USER / CBD_PW from .env afterwards.
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

LOGIN_URL = "https://www.cbbdata.com/api/auth/login"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def main() -> int:
    load_dotenv(ENV_PATH)
    user, pw = os.getenv("CBD_USER"), os.getenv("CBD_PW")
    if not user or not pw:
        print("Set CBD_USER and CBD_PW in .env first.", file=sys.stderr)
        return 1

    try:
        resp = requests.post(LOGIN_URL, json={"username": user, "password": pw}, timeout=30)
    except requests.RequestException:
        print("Could not reach cbbdata. Check your connection and try again.", file=sys.stderr)
        return 1
    if resp.status_code != 200:
        print(f"Login failed (HTTP {resp.status_code}). Check your username and password.",
              file=sys.stderr)
        return 1

    body = resp.json()
    # The R client takes the first value of the response object.
    key = next(iter(body.values())) if isinstance(body, dict) else body[0]
    if not isinstance(key, str) or not key:
        print("Login succeeded but no API key was found in the response.", file=sys.stderr)
        return 1

    ENV_PATH.touch(exist_ok=True)
    set_key(str(ENV_PATH), "CBBDATA_API_KEY", key)
    print(f"API key saved to {ENV_PATH.name} as CBBDATA_API_KEY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
