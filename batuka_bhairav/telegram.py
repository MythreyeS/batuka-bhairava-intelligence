# batuka_bhairav/telegram.py

import os
import requests
from typing import Optional


def send_telegram(
    message: str,
    parse_mode: Optional[str] = None,
    disable_preview: bool = True
) -> dict:
    """
    Sends a Telegram message using bot token + chat ID from environment variables.

    Environment Variables Required:
        TELEGRAM_TOKEN
        TELEGRAM_CHAT_ID

    Returns:
        Telegram API JSON response
    """

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise ValueError("❌ TELEGRAM_TOKEN not set in environment variables.")

    if not chat_id:
        raise ValueError("❌ TELEGRAM_CHAT_ID not set in environment variables.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": disable_preview,
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"🚨 Telegram API request failed: {e}")
