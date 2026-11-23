"""Client for the cbbdata API (Barttorvik data).

Endpoints and auth format come from the official R client
(github.com/andreweatherman/cbbdata): the key goes in a `key` query param,
filters are query params matching column names, and player endpoints return
Parquet bytes.
"""

import io
import logging
import os

import pandas as pd
import requests
from dotenv import load_dotenv

from data import cache

BASE_URL = "https://www.cbbdata.com/api/"
TIMEOUT_SECONDS = 60
SPLIT_TYPES = ("location", "game_type", "month", "game_result")

log = logging.getLogger(__name__)


class CbbdataError(Exception):
    """Base error. Messages are safe to show to users (no API key)."""


class DataSourceError(CbbdataError):
    """The API was unreachable, rejected the request, or returned bad data."""


class PlayerNotFound(CbbdataError):
    """The request succeeded but no matching player was found."""


def _api_key() -> str:
    load_dotenv()
    key = os.getenv("CBBDATA_API_KEY", "").strip()
    if not key:
        raise DataSourceError(
            "CBBDATA_API_KEY is not set. Add it to .env (see .env.example)."
        )
    return key


def _redact(text: str, key: str) -> str:
    return text.replace(key, "***") if key else text


def fetch(endpoint: str, use_cache: bool = True, **params) -> pd.DataFrame:
    """GET a cbbdata endpoint and return it as a DataFrame.

    Non-empty responses are cached to disk. Empty ones are not, since an
    in-progress season will fill in later.
    """
    params = {k: v for k, v in params.items() if v is not None}

    if use_cache:
        cached = cache.get(endpoint, params)
        if cached is not None:
            log.info("cache hit: %s %s", endpoint, params)
            return pd.read_parquet(io.BytesIO(cached))

    key = _api_key()
    log.info("fetching: %s %s", endpoint, params)
    try:
        resp = requests.get(
            BASE_URL + endpoint,
            params={**params, "key": key},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as e:
        raise DataSourceError(
            f"Could not reach cbbdata: {_redact(str(e), key)}"
        ) from None

    if resp.status_code != 200:
        try:
            detail = resp.json().get("message", "")
        except ValueError:
            detail = ""
        raise DataSourceError(
            _redact(f"cbbdata returned HTTP {resp.status_code}. {detail}".strip(), key)
        )

    try:
        df = pd.read_parquet(io.BytesIO(resp.content))
    except Exception:
        snippet = _redact(resp.text[:200], key) if resp.content else "(empty body)"
        raise DataSourceError(
            f"cbbdata returned data that isn't Parquet: {snippet}"
        ) from None

    if not df.empty:
        cache.put(endpoint, params, resp.content)
    return df


def player_season(**filters) -> pd.DataFrame:
    """Season averages. Filter on year, team, player, or any column."""
    return fetch("torvik/player/season", **filters)


def player_games(**filters) -> pd.DataFrame:
    """Per-game logs. Filter on year, team, player, or any column."""
    return fetch("torvik/player/game", **filters)


def player_splits(split: str, **filters) -> pd.DataFrame:
    """Season averages split by location, game_type, month, or game_result."""
    if split not in SPLIT_TYPES:
        raise ValueError(f"split must be one of {SPLIT_TYPES}")
    return fetch("torvik/player/splits", split=split, **filters)
