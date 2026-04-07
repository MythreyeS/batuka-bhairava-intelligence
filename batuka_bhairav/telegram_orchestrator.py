# batuka_bhairav/telegram_orchestrator.py
# ✅ FIXED: Retry logic with exponential backoff (BRD Section 8.1)
 
"""
Telegram message delivery with robust retry mechanism.
Per BRD Section 8.1: 3 retry attempts with exponential backoff (2s/4s/8s)
"""
 
from __future__ import annotations
import requests
import logging
import time
from batuka_bhairav.config import (
    TELEGRAM_RETRY_ATTEMPTS, TELEGRAM_RETRY_BACKOFF, TELEGRAM_TIMEOUT
)
 
logger = logging.getLogger("batuka_telegram")
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEND WITH RETRY & BACKOFF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def send_telegram_message(
    message: str,
    telegram_token: str,
    telegram_chat_id: str,
    max_retries: int = TELEGRAM_RETRY_ATTEMPTS,
    backoff_schedule: list[int] = TELEGRAM_RETRY_BACKOFF
) -> bool:
    """
    ✅ FIXED: Send Telegram message with retry and exponential backoff
    
    Per BRD Section 8.1:
    Telegram delivery with retry on failure
    3 attempts, exponential backoff (2s/4s/8s)
    
    Args:
        message: HTML-formatted message
        telegram_token: Bot token (from env)
        telegram_chat_id: Chat ID (from env)
        max_retries: Number of retry attempts
        backoff_schedule: Wait times between retries in seconds
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    if not telegram_token or not telegram_chat_id:
        logger.error("❌ Telegram credentials missing")
        return False
    
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    
    payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        "parse_mode": "HTML",
    }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RETRY LOOP
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    for attempt in range(max_retries):
        try:
            logger.info(f"📤 Telegram send (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(
                url,
                json=payload,
                timeout=TELEGRAM_TIMEOUT
            )
            
            # ✅ FIXED: Check response status
            if response.status_code == 200:
                logger.info(f"✅ Telegram sent successfully")
                return True
            else:
                # API error
                error_msg = response.json().get("description", "Unknown error")
                logger.warning(f"❌ Telegram API error: {error_msg}")
                
                # Permanent errors shouldn't retry
                if response.status_code in [401, 403, 404]:
                    logger.error(f"❌ Permanent error: {response.status_code}")
                    return False
        
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Telegram timeout (attempt {attempt + 1})")
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"⚠️ Connection error: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
            return False
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BACKOFF IF NOT LAST ATTEMPT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if attempt < max_retries - 1:
            wait_time = backoff_schedule[attempt] if attempt < len(backoff_schedule) else 8
            logger.info(f"⏳ Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    logger.error(f"❌ Failed to send after {max_retries} attempts")
    return False
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEND MULTIPLE MESSAGES (for multi-market)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def send_telegram_messages(
    messages: dict[str, str],
    telegram_token: str,
    telegram_chat_id: str
) -> dict[str, bool]:
    """
    ✅ NEW: Send multiple messages (one per market)
    
    Args:
        messages: Dict {market_code: message}
        telegram_token: Bot token
        telegram_chat_id: Chat ID
    
    Returns:
        Dict {market_code: success}
    """
    
    results = {}
    
    for market_code, message in messages.items():
        logger.info(f"📤 Sending for {market_code}...")
        success = send_telegram_message(
            message,
            telegram_token,
            telegram_chat_id
        )
        results[market_code] = success
        
        # Small delay between messages to avoid rate limiting
        time.sleep(2)
    
    return results
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def check_telegram_connection(telegram_token: str) -> bool:
    """
    ✅ Verify Telegram bot token is valid
    
    Returns:
        bool: True if token is valid
    """
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json().get("result", {})
            logger.info(f"✅ Telegram bot verified: {bot_info.get('username', 'unknown')}")
            return True
        else:
            logger.error(f"❌ Invalid Telegram token")
            return False
    
    except Exception as e:
        logger.error(f"❌ Cannot reach Telegram: {e}")
        return False
