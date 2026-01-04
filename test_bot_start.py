#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple test to verify telegram_bot.py can start"""

import sys
import os

print("=" * 60)
print("TEST: Checking if telegram_bot.py can be imported...")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
print()

# Check if file exists
bot_file = os.path.join(os.path.dirname(__file__), "telegram_bot.py")
print(f"Looking for: {bot_file}")
print(f"File exists: {os.path.exists(bot_file)}")
print()

if os.path.exists(bot_file):
    print("Attempting to import telegram_bot...")
    try:
        import telegram_bot
        print("✓ Import successful!")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("✗ telegram_bot.py not found!")

print()
print("=" * 60)
input("Press Enter to exit...")

