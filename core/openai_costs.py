import os
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional

import requests


OPENAI_COSTS_URL = "https://api.openai.com/v1/organization/costs"
SECONDS_PER_DAY = 24 * 60 * 60


def unix_now() -> int:
    return int(time.time())


def unix_start_of_today_utc() -> int:
    now = datetime.now(timezone.utc)
    start = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        tzinfo=timezone.utc,
    )
    return int(start.timestamp())


def unix_start_of_tomorrow_utc() -> int:
    today_start = datetime.fromtimestamp(
        unix_start_of_today_utc(),
        tz=timezone.utc,
    )

    tomorrow_start = today_start + timedelta(days=1)
    return int(tomorrow_start.timestamp())


def default_cost_window_end(start_time: int) -> int:
    """
    The costs endpoint validates that end_date comes after start_date.
    So for a same-day cost snapshot, use the next UTC day as end_time.
    """
    return start_time + SECONDS_PER_DAY


def fetch_openai_cost_usd(
    start_time: int,
    end_time: Optional[int] = None,
) -> Decimal:
    """
    Fetch official OpenAI organization cost in USD.

    Requires:
        OPENAI_ADMIN_KEY=sk-admin-...

    Usage for this script:
        cost_before = total API cost since UTC start of today
        cost_after  = total API cost since UTC start of today
        run_cost    = cost_after - cost_before
    """

    admin_key = os.getenv("OPENAI_ADMIN_KEY")

    if not admin_key:
        raise RuntimeError("Missing OPENAI_ADMIN_KEY. Add it to your .env file.")

    if end_time is None:
        end_time = default_cost_window_end(start_time)

    # The endpoint complains if end_date is not after start_date.
    # Adding only 60 seconds is not enough if both timestamps are on the same UTC date.
    if end_time <= start_time:
        end_time = default_cost_window_end(start_time)

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "limit": 180,
    }

    headers = {
        "Authorization": f"Bearer {admin_key}",
    }

    response = requests.get(
        OPENAI_COSTS_URL,
        headers=headers,
        params=params,
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenAI costs request failed: {response.status_code} {response.text}"
        )

    data = response.json()
    total_usd = Decimal("0")

    for bucket in data.get("data", []):
        for result in bucket.get("results", []):
            amount = result.get("amount") or {}
            currency = amount.get("currency")
            value = amount.get("value")

            if currency == "usd" and value is not None:
                total_usd += Decimal(str(value))

    return total_usd