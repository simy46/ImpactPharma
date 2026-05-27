import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import requests
from dotenv import load_dotenv

from core.log_manager import LogManager


load_dotenv()


def unix_start_of_today_utc() -> int:
    now = datetime.now(timezone.utc)
    start = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        tzinfo=timezone.utc,
    )

    return int(start.timestamp())


def fetch_openai_cost_usd(start_time: int) -> Optional[Decimal]:
    api_key = os.getenv("OPENAI_ADMIN_KEY")

    if not api_key:
        return None

    url = "https://api.openai.com/v1/organization/costs"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    params = {
        "start_time": start_time,
        "limit": 1,
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()
    total = Decimal("0")

    for bucket in payload.get("data", []):
        for result in bucket.get("results", []):
            amount = result.get("amount", {})
            value = amount.get("value")

            if value is not None:
                total += Decimal(str(value))

    return total


def safe_fetch_openai_cost_usd(
    logger: LogManager,
    label: str,
    start_time: int,
) -> Optional[Decimal]:
    try:
        value = fetch_openai_cost_usd(start_time=start_time)

        if value is None:
            logger.write("info", f"{label}: Unavailable. Missing OPENAI_ADMIN_API_KEY.")
        else:
            logger.write("info", f"{label}: ${value:.6f}")

        return value

    except requests.HTTPError as e:
        error_detail = ""

        try:
            error_detail = f" | {e.response.text}"
        except Exception:
            pass

        logger.write("warn", f"{label} unavailable: {e}{error_detail}")
        return None

    except Exception as e:
        logger.write("warn", f"{label} unavailable: {e}")
        return None