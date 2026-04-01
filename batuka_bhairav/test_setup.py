#!/usr/bin/env python3
"""
🧪 TEST SCRIPT FOR run_all_markets.py
Verifies all dependencies and configuration before running
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """Check environment variables"""
    logger.info("\n📋 CHECKING ENVIRONMENT VARIABLES...")
    
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token:
        logger.error("❌ TELEGRAM_TOKEN not set")
        return False
    else:
        logger.info(f"✅ TELEGRAM_TOKEN: {token[:10]}...{token[-5:]}")
    
    if not chat_id:
        logger.error("❌ TELEGRAM_CHAT_ID not set")
        return False
    else:
        logger.info(f"✅ TELEGRAM_CHAT_ID: {chat_id}")
    
    return True


def test_imports():
    """Check all required imports"""
    logger.info("\n📦 CHECKING IMPORTS...")
    
    imports_to_check = [
        ("batuka_bhairav.config", "Batuka config"),
        ("batuka_bhairav.universe.fetch_universe", "Universe fetchers"),
        ("batuka_bhairav.universe.market_data", "Market data"),
        ("batuka_bhairav.core.scoring", "Scoring engine"),
        ("batuka_bhairav.core.sector", "Sector analysis"),
        ("batuka_bhairav.core.regime", "Regime detection"),
        ("batuka_bhairav.telegram_orchestrator", "Telegram sender"),
    ]
    
    all_ok = True
    for module_name, description in imports_to_check:
        try:
            __import__(module_name)
            logger.info(f"✅ {description}: {module_name}")
        except ImportError as e:
            logger.error(f"❌ {description}: {module_name}")
            logger.error(f"   Error: {e}")
            all_ok = False
    
    return all_ok


def test_telegram():
    """Test Telegram connection"""
    logger.info("\n📤 TESTING TELEGRAM CONNECTION...")
    
    try:
        from batuka_bhairav.telegram_orchestrator import send_telegram_message
        
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        msg = "🧪 Testing Batuka! This is a test message."
        logger.info(f"Sending test message...")
        
        result = send_telegram_message(msg, token, chat_id)
        
        if result:
            logger.info("✅ Telegram connection working!")
            return True
        else:
            logger.error("❌ Telegram failed to send")
            return False
    
    except Exception as e:
        logger.error(f"❌ Telegram test error: {e}")
        return False


def test_universe_files():
    """Check universe CSV files"""
    logger.info("\n📊 CHECKING UNIVERSE FILES...")
    
    required_files = [
        "batuka_bhairav/universe/nifty500.csv",
        "batuka_bhairav/universe/usa500.csv",
        "batuka_bhairav/universe/ftse100.csv",
        "batuka_bhairav/universe/sgx.csv",
    ]
    
    all_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            logger.info(f"✅ {file_path} ({size} bytes)")
        else:
            logger.error(f"❌ {file_path} NOT FOUND")
            all_ok = False
    
    return all_ok


def test_universe_fetch():
    """Test fetching universe data"""
    logger.info("\n🌍 TESTING UNIVERSE FETCH...")
    
    try:
        from batuka_bhairav.universe.fetch_universe import (
            fetch_nse500, fetch_sp500, fetch_ftse100, fetch_sgx
        )
        
        logger.info("Fetching India NSE500...")
        in_stocks = fetch_nse500()
        logger.info(f"✅ India: {len(in_stocks)} stocks")
        
        logger.info("Fetching USA S&P500...")
        us_stocks = fetch_sp500()
        logger.info(f"✅ USA: {len(us_stocks)} stocks")
        
        logger.info("Fetching UK FTSE100...")
        uk_stocks = fetch_ftse100()
        logger.info(f"✅ UK: {len(uk_stocks)} stocks")
        
        logger.info("Fetching Singapore STI...")
        sg_stocks = fetch_sgx()
        logger.info(f"✅ Singapore: {len(sg_stocks)} stocks")
        
        if in_stocks and us_stocks and uk_stocks:
            return True
        else:
            logger.warning("⚠️ Some universes are empty")
            return False
    
    except Exception as e:
        logger.error(f"❌ Universe fetch error: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("🧪 BATUKA TEST SUITE")
    logger.info("=" * 70)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Python Imports", test_imports),
        ("Universe Files", test_universe_files),
        ("Universe Fetch", test_universe_fetch),
        ("Telegram Connection", test_telegram),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUMMARY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n" + "=" * 70)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 70)
        logger.info("\n✅ You're ready to run: python run_all_markets.py\n")
        return 0
    else:
        logger.info("\n" + "=" * 70)
        logger.info("⚠️ SOME TESTS FAILED")
        logger.info("=" * 70)
        logger.info("\nFix the issues above and try again.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
