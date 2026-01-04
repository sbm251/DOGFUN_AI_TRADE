import os
import json
import requests
from datetime import datetime

def get_telegram_credentials():
    """Get Telegram bot token and chat ID from files"""
    # Try multiple locations
    search_paths = [
        os.path.dirname(os.path.abspath(__file__)),  # Current directory
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Parent directory
    ]
    
    # Also try going up a few levels
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        search_paths.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    
    bot_token = ""
    chat_id = ""
    
    for base_dir in search_paths:
        token_path = os.path.join(base_dir, "telegram_token.txt")
        chat_id_path = os.path.join(base_dir, "telegram_chat_id.txt")
        
        if os.path.exists(token_path) and not bot_token:
            try:
                with open(token_path, 'r', encoding='utf-8-sig') as f:
                    bot_token = f.read().strip()
            except:
                pass
        
        if os.path.exists(chat_id_path) and not chat_id:
            try:
                with open(chat_id_path, 'r', encoding='utf-8-sig') as f:
                    chat_id = f.read().strip()
            except:
                pass
        
        if bot_token and chat_id:
            break
    
    return bot_token, chat_id

def _load_notification_settings():
    """Load notification preferences"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(base_dir, "telegram_notification_settings.json")
    
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Default settings - all enabled
    return {
        "notify_training": True,
        "notify_trades": True,
        "notify_profit_loss": True,
        "daily_report": True
    }

def send_telegram_message(text, parse_mode="HTML"):
    """Send a message to Telegram"""
    bot_token, chat_id = get_telegram_credentials()
    
    if not bot_token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def notify_training_complete(coin, message=""):
    """Notify when training is complete"""
    settings = _load_notification_settings()
    if not settings.get("notify_training", True):
        return
    
    text = f"🎓 <b>Training Complete</b>\n\n"
    text += f"Coin: <b>{coin}</b>\n"
    if message:
        text += f"Status: {message}\n"
    text += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    send_telegram_message(text)

def notify_trade_executed(side, symbol, quantity, price, profit_loss=None):
    """Notify when a trade is executed"""
    settings = _load_notification_settings()
    if not settings.get("notify_trades", True):
        return
    
    side_icon = "🟢" if side == "BUY" else "🔴"
    side_text = "BUY" if side == "BUY" else "SELL"
    
    text = f"{side_icon} <b>Trade Executed</b>\n\n"
    text += f"Type: <b>{side_text}</b>\n"
    text += f"Symbol: <b>{symbol}</b>\n"
    text += f"Quantity: {quantity:.4f}\n"
    if price:
        text += f"Price: {price:.2f} EUR\n"
        text += f"Value: {quantity * price:.2f} EUR\n"
    
    if profit_loss is not None and settings.get("notify_profit_loss", True):
        if profit_loss > 0:
            text += f"\n💰 <b>Profit: +{profit_loss:.2f} EUR</b> ✅"
        elif profit_loss < 0:
            text += f"\n📉 <b>Loss: {profit_loss:.2f} EUR</b> ❌"
        else:
            text += f"\n⚖️ <b>Break Even</b>"
    
    text += f"\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    send_telegram_message(text)

def notify_profit_loss(symbol, profit_loss, percentage=None):
    """Notify about profit/loss for a position"""
    settings = _load_notification_settings()
    if not settings.get("notify_profit_loss", True):
        return
    
    if profit_loss > 0:
        icon = "💰"
        text = f"{icon} <b>Profit Alert</b>\n\n"
        text += f"Symbol: <b>{symbol}</b>\n"
        text += f"Profit: <b>+{profit_loss:.2f} EUR</b> ✅\n"
        if percentage:
            text += f"Percentage: <b>+{percentage:.2f}%</b>\n"
    elif profit_loss < 0:
        icon = "📉"
        text = f"{icon} <b>Loss Alert</b>\n\n"
        text += f"Symbol: <b>{symbol}</b>\n"
        text += f"Loss: <b>{profit_loss:.2f} EUR</b> ❌\n"
        if percentage:
            text += f"Percentage: <b>{percentage:.2f}%</b>\n"
    else:
        return  # Don't notify for break-even
    
    text += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    send_telegram_message(text)

def notify_daily_summary(total_value, profit_loss_today, trades_today):
    """Notify daily summary"""
    settings = _load_notification_settings()
    if not settings.get("daily_report", True):
        return
    
    text = f"📊 <b>Daily Summary</b>\n\n"
    text += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    text += f"💰 Total Value: {total_value:.2f} EUR\n"
    
    if profit_loss_today > 0:
        text += f"📈 Today's Profit: <b>+{profit_loss_today:.2f} EUR</b> ✅\n"
    elif profit_loss_today < 0:
        text += f"📉 Today's Loss: <b>{profit_loss_today:.2f} EUR</b> ❌\n"
    else:
        text += f"⚖️ Today's P/L: {profit_loss_today:.2f} EUR\n"
    
    text += f"📊 Trades Today: {trades_today}\n"
    text += f"\nTime: {datetime.now().strftime('%H:%M:%S')}"
    
    send_telegram_message(text)
