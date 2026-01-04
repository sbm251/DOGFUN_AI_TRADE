"""Test script to debug Telegram code sending"""
import os
import sys
import requests
import random

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

base_dir = os.path.dirname(os.path.abspath(__file__))
token_path = os.path.join(base_dir, "telegram_token.txt")
chat_id_path = os.path.join(base_dir, "telegram_chat_id.txt")

print("=== Telegram Code Sending Test ===\n")

# Check files
if not os.path.exists(token_path):
    print("ERROR: telegram_token.txt not found")
    exit(1)
if not os.path.exists(chat_id_path):
    print("ERROR: telegram_chat_id.txt not found")
    exit(1)

# Read credentials
with open(token_path, 'r', encoding='utf-8') as f:
    bot_token = f.read().strip()
with open(chat_id_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
    chat_id = f.read().strip()

print(f"Token: {bot_token[:10]}... (length: {len(bot_token)})")
print(f"Chat ID: {chat_id}")

if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("\nERROR: Token is empty or placeholder!")
    exit(1)
if not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID_HERE":
    print("\nERROR: Chat ID is empty or placeholder!")
    exit(1)

# Generate test code
code = str(random.randint(100000, 999999))
print(f"\nGenerated code: {code}")

# Send via Telegram
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
message = f"🔐 PowerTrader AI Authentication Code\n\nYour login code is:\n\n{code}\n\nValid for 5 minutes."
payload = {
    "chat_id": chat_id,
    "text": message
}

print(f"\nSending to: {url}")
print(f"Message: {message[:50]}...")

try:
    resp = requests.post(url, json=payload, timeout=10)
    print(f"\nResponse status: {resp.status_code}")
    resp_data = resp.json()
    print(f"Response: {resp_data}")
    
    if resp.status_code == 200 and resp_data.get("ok"):
        print("\n✓ SUCCESS: Code sent to Telegram!")
        print(f"Check your Telegram for code: {code}")
    else:
        print(f"\n✗ FAILED: {resp_data.get('description', 'Unknown error')}")
        if resp_data.get("error_code") == 400:
            print("  → Bad Request: Check chat_id format")
        elif resp_data.get("error_code") == 401:
            print("  → Unauthorized: Check bot token")
        elif resp_data.get("error_code") == 403:
            print("  → Forbidden: Bot may be blocked or chat_id wrong")
except Exception as e:
    print(f"\n✗ ERROR: {e}")

