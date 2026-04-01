import requests
import time


def send_telegram_message(message: str, token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    # 🔁 Retry logic
    for attempt in range(3):
        try:
            response = requests.post(url, data=payload, timeout=10)

            if response.status_code == 200:
                print("✅ Telegram message sent")
                return True
            else:
                print(f"⚠️ Telegram failed: {response.text}")

        except Exception as e:
            print(f"⚠️ Error sending Telegram: {e}")

        time.sleep(2 ** attempt)  # exponential backoff

    print("❌ Telegram failed after retries")
    return False
