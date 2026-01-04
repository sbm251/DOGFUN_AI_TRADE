# CRITICAL: Print immediately to verify script is running
print("SCRIPT STARTED", flush=True)
import sys
sys.stdout.flush()
sys.stderr.flush()

try:
    import os
    import json
    import time
    import requests
    from datetime import datetime, timedelta
    
    print("=" * 60, flush=True)
    print("TELEGRAM BOT STARTING - DEBUG MODE", flush=True)
    print("=" * 60, flush=True)
    print(f"Python version: {sys.version}", flush=True)
    print(f"Working directory: {os.getcwd()}", flush=True)
    try:
        print(f"Script location: {__file__}", flush=True)
    except:
        print("Script location: (could not determine)", flush=True)
    sys.stdout.flush()
except Exception as e:
    print(f"ERROR in imports: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    raise

# Try to import PowerTrader with error handling
print("\n[STEP 1] Attempting to import PowerTrader...")
sys.stdout.flush()
try:
    from pt_trader import PowerTrader
    print("[IMPORT] ✓ PowerTrader imported successfully")
    sys.stdout.flush()
except ImportError as e:
    print(f"[IMPORT ERROR] ✗ Failed to import PowerTrader: {e}")
    print("[IMPORT] Bot will run but trading features may not work")
    sys.stdout.flush()
    PowerTrader = None
except Exception as e:
    print(f"[IMPORT ERROR] ✗ Unexpected error importing PowerTrader: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    PowerTrader = None

class TelegramBot:
    def __init__(self):
        try:
            print("[INIT] Starting bot initialization...")
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"[INIT] Base directory: {self.base_dir}")
            
            raw_token = self._load_token()
            # Clean token of any BOM or invalid characters
            self.bot_token = self._clean_token(raw_token) if raw_token else ""
            print(f"[INIT] Token loaded: {'Yes' if self.bot_token else 'No'}")
            
            self.chat_id = self._load_chat_id()
            print(f"[INIT] Chat ID loaded: {'Yes' if self.chat_id else 'No'}")
            
            if PowerTrader is None:
                print("[INIT WARNING] PowerTrader not available, some features will be disabled")
                self.trader = None
            else:
                print("[INIT] Initializing PowerTrader...")
                try:
                    self.trader = PowerTrader()
                    print("[INIT] PowerTrader initialized successfully")
                except Exception as e:
                    print(f"[INIT ERROR] Failed to initialize PowerTrader: {e}")
                    import traceback
                    traceback.print_exc()
                    print("[INIT] Continuing without PowerTrader (some features disabled)")
                    self.trader = None
            
            self.last_update_id = 0
            self.running = True
            self.waiting_for_input = {}  # Track users waiting for input
            self.daily_report_sent = False
            self.last_daily_report_date = None
            # Cache for performance
            self._cache = {}
            self._cache_timeout = 5  # Cache for 5 seconds
            self._last_cache_time = {}
            print("[INIT] Bot initialization complete!")
        except Exception as e:
            print(f"[INIT ERROR] Failed to initialize bot: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _clean_token(self, token):
        """Clean token of any BOM or invalid characters"""
        if not token:
            return ""
        # Remove BOM characters (both Unicode and bytes representation)
        token = token.replace('\ufeff', '')
        # Remove any non-printable characters except colon, underscore, numbers, and letters
        # Telegram bot tokens can contain: numbers, letters, colons, and underscores
        token = ''.join(c for c in token if c.isalnum() or c == ':' or c == '_')
        return token.strip()
    
    def _load_token(self):
        token_path = os.path.join(self.base_dir, "telegram_token.txt")
        print(f"[LOAD] Looking for token file: {token_path}")
        print(f"[LOAD] File exists: {os.path.exists(token_path)}")
        sys.stdout.flush()
        
        if os.path.exists(token_path):
            try:
                # Read as binary first to check for BOM
                with open(token_path, 'rb') as f:
                    data = f.read()
                    print(f"[LOAD] Token file read, size: {len(data)} bytes")
                    sys.stdout.flush()
                    
                    # Remove UTF-8 BOM if present
                    if data.startswith(b'\xef\xbb\xbf'):
                        print("[LOAD] Removing BOM from token...")
                        sys.stdout.flush()
                        data = data[3:]
                    
                    # Decode and clean
                    token = data.decode('utf-8').strip()
                    # Remove any remaining non-printable characters except colon, underscore, numbers/letters
                    # Telegram bot tokens can contain: numbers, letters, colons, and underscores
                    token = ''.join(c for c in token if c.isalnum() or c == ':' or c == '_')
                    token = token.strip()
                    
                    # Final validation - ensure no BOM characters
                    if '\ufeff' in token:
                        token = token.replace('\ufeff', '')
                    
                    if token:
                        print(f"[LOAD] ✓ Token loaded successfully (length: {len(token)})")
                    else:
                        print("[LOAD WARNING] Token file exists but is empty or invalid")
                    sys.stdout.flush()
                    return token
            except Exception as e:
                print(f"[LOAD ERROR] Error loading token: {e}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
                return ""
        else:
            print(f"[LOAD ERROR] Token file not found at: {token_path}")
            sys.stdout.flush()
        return ""
    
    def _load_chat_id(self):
        chat_id_path = os.path.join(self.base_dir, "telegram_chat_id.txt")
        print(f"[LOAD] Looking for chat_id file: {chat_id_path}")
        print(f"[LOAD] File exists: {os.path.exists(chat_id_path)}")
        sys.stdout.flush()
        if os.path.exists(chat_id_path):
            try:
                with open(chat_id_path, 'r', encoding='utf-8-sig') as f:
                    chat_id = f.read().strip()
                    if chat_id:
                        print(f"[LOAD] ✓ Chat ID loaded: {chat_id}")
                    else:
                        print("[LOAD WARNING] Chat ID file exists but is empty")
                    sys.stdout.flush()
                    return chat_id
            except Exception as e:
                print(f"[LOAD ERROR] Error loading chat_id: {e}")
                sys.stdout.flush()
                return ""
        else:
            print(f"[LOAD ERROR] Chat ID file not found at: {chat_id_path}")
            sys.stdout.flush()
        return ""
    
    def _load_gui_settings(self):
        settings_path = os.path.join(self.base_dir, "gui_settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_gui_settings(self, settings):
        settings_path = os.path.join(self.base_dir, "gui_settings.json")
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _load_notification_settings(self):
        """Load notification preferences"""
        settings_path = os.path.join(self.base_dir, "telegram_notification_settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        # Default settings
        return {
            "notify_training": True,
            "notify_trades": True,
            "notify_profit_loss": True,
            "daily_report": True,
            "daily_report_time": "09:00"  # 9 AM
        }
    
    def _save_notification_settings(self, settings):
        """Save notification preferences"""
        settings_path = os.path.join(self.base_dir, "telegram_notification_settings.json")
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving notification settings: {e}")
    
    def get_logo_path(self):
        """Get the path to the logo image"""
        logo_path = os.path.join(self.base_dir, "image.png")
        if os.path.exists(logo_path):
            return logo_path
        return None
    
    def send_message(self, text, reply_markup=None, chat_id=None):
        """Send a text message"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id or self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, json=payload, timeout=10)  # Increased to 10 seconds
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def send_photo(self, photo_path, caption=None, reply_markup=None, chat_id=None):
        """Send a photo"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo_file:
                files = {
                    'photo': (os.path.basename(photo_path), photo_file, 'image/png')
                }
                data = {
                    'chat_id': chat_id or self.chat_id
                }
                if caption:
                    data['caption'] = caption
                if reply_markup:
                    data['reply_markup'] = json.dumps(reply_markup)
                
                response = requests.post(url, files=files, data=data, timeout=10)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error sending photo: {e}")
            return None
    
    def get_main_menu(self):
        """Generate main menu keyboard"""
        return {
            "inline_keyboard": [
                [{"text": "📊 Account Status", "callback_data": "account"}],
                [{"text": "💰 Profits & Losses", "callback_data": "profits"}],
                [{"text": "📈 Current Trades", "callback_data": "trades"}],
                [{"text": "🎓 Training Status", "callback_data": "training"}],
                [{"text": "📜 Trade History", "callback_data": "history"}],
                [{"text": "📊 Daily Report", "callback_data": "daily_report"}],
                [{"text": "🔧 Settings", "callback_data": "settings"}],
                [{"text": "ℹ️ About", "callback_data": "about"}]
            ]
        }
    
    def get_settings_menu(self):
        """Generate settings menu keyboard"""
        notif_settings = self._load_notification_settings()
        gui_settings = self._load_gui_settings()
        
        training_icon = "✅" if notif_settings.get("notify_training", True) else "❌"
        trades_icon = "✅" if notif_settings.get("notify_trades", True) else "❌"
        profit_icon = "✅" if notif_settings.get("notify_profit_loss", True) else "❌"
        daily_icon = "✅" if notif_settings.get("daily_report", True) else "❌"
        
        return {
            "inline_keyboard": [
                [{"text": f"{training_icon} Training Updates", "callback_data": "toggle_training"}],
                [{"text": f"{trades_icon} Trade Notifications", "callback_data": "toggle_trades"}],
                [{"text": f"{profit_icon} Profit/Loss Alerts", "callback_data": "toggle_profit_loss"}],
                [{"text": f"{daily_icon} Daily Reports", "callback_data": "toggle_daily_report"}],
                [{"text": f"💵 Trade Amount: {gui_settings.get('fixed_trade_amount', 6)} EUR", "callback_data": "set_trade_amount"}],
                [{"text": f"💰 Min Purchase: {gui_settings.get('min_trade_size', 10)} EUR", "callback_data": "set_min_purchase"}],
                [{"text": f"📊 Trade Allocation: {gui_settings.get('trade_allocation_pct', 10)}%", "callback_data": "set_allocation"}],
                [{"text": "⬅️ Back to Menu", "callback_data": "back_to_menu"}]
            ]
        }
    
    def format_account_status(self):
        """Format account status message - with caching"""
        if not self.trader:
            return "❌ Error: PowerTrader not initialized. Check bot logs."
        
        # Try cache first
        cached = self._get_cached_data("account_status")
        if cached:
            return cached
        
        account = self.trader.get_account()
        if not account:
            return "❌ Error retrieving account information"
        
        holdings = self.trader.get_holdings()
        holdings_value = 0
        for holding in holdings[:8]:  # Reduced from 10 to 8
            asset = holding['asset']
            quantity = holding['free'] + holding['locked']
            if quantity > 0.0001:
                try:
                    price = self.trader.get_price(asset)
                    if price:
                        holdings_value += quantity * price
                except:
                    pass
        
        total_value = account['balance'] + holdings_value
        
        message = "📊 <b>Account Status</b>\n\n"
        message += f"💰 Total Value: <b>{total_value:.2f} EUR</b>\n"
        message += f"💵 EUR Balance: {account['balance']:.2f} EUR\n"
        message += f"💎 Holdings Value: {holdings_value:.2f} EUR\n"
        message += f"💪 Buying Power: {account['buying_power']:.2f} EUR\n"
        message += f"💵 Trade Amount: {self.trader.fixed_trade_amount if self.trader else 6} EUR per trade\n"
        message += f"📈 Trade Allocation: {account['trade_allocation_pct']}%\n"
        message += f"💼 Min Trade Size: {account['min_trade_size']} EUR\n"
        message += f"📦 Active Holdings: {len(holdings)}"
        
        # Cache the result
        self._set_cached_data("account_status", message)
        return message
    
    def format_profits(self):
        """Format profits and losses message - with caching"""
        if not self.trader:
            return "❌ Error: PowerTrader not initialized. Check bot logs."
        
        cached = self._get_cached_data("profits")
        if cached:
            return cached
        
        holdings = self.trader.get_holdings()
        if not holdings:
            return "💰 <b>Profits & Losses</b>\n\nNo active positions"
        
        message = "💰 <b>Profits & Losses</b>\n\n"
        total_value = 0
        
        for holding in holdings[:10]:  # Reduced from 15 to 10
            asset = holding['asset']
            quantity = holding['free'] + holding['locked']
            if quantity > 0.0001:
                try:
                    price = self.trader.get_price(asset)
                    if price:
                        value = quantity * price
                        total_value += value
                        message += f"{asset}: {quantity:.4f} @ {price:.2f} EUR = {value:.2f} EUR\n"
                except:
                    pass
        
        message += f"\n💎 <b>Total Portfolio Value: {total_value:.2f} EUR</b>"
        self._set_cached_data("profits", message)
        return message
    
    def format_current_trades(self):
        """Format current trades message - with caching"""
        if not self.trader:
            return "❌ Error: PowerTrader not initialized. Check bot logs."
        
        cached = self._get_cached_data("current_trades")
        if cached:
            return cached
        
        holdings = self.trader.get_holdings()
        if not holdings:
            return "📈 <b>Current Trades</b>\n\nNo active positions"
        
        message = "📈 <b>Current Trades</b>\n\n"
        for holding in holdings[:10]:  # Reduced from 15 to 10
            symbol = holding['asset']
            quantity = holding['free']
            locked = holding['locked']
            total = quantity + locked
            if total > 0.0001:
                try:
                    price = self.trader.get_price(symbol)
                    if price:
                        value = total * price
                        message += f"<b>{symbol}</b>:\n"
                        message += f"  Quantity: {total:.4f}\n"
                        message += f"  Price: {price:.2f} EUR\n"
                        message += f"  Value: {value:.2f} EUR\n"
                        if locked > 0:
                            message += f"  ⚠️ Locked: {locked:.4f}\n"
                        message += "\n"
                except:
                    message += f"<b>{symbol}</b>: {total:.4f}\n\n"
        
        self._set_cached_data("current_trades", message)
        return message
    
    def format_training_status(self):
        """Format training status message"""
        message = "🎓 <b>Training Status</b>\n\n"
        
        # Check for trainer status files
        settings = self._load_gui_settings()
        main_dir = settings.get("main_neural_dir", self.base_dir)
        if not main_dir:
            main_dir = self.base_dir
        
        coins = settings.get("coins", [])
        if not coins:
            return message + "No coins configured for training."
        
        trained_coins = []
        not_trained_coins = []
        training_coins = []
        
        for coin in coins[:15]:  # Limit to first 15 coins
            if not coin or not coin.strip():
                continue
            coin = coin.strip().upper()
            
            # Determine coin directory
            if coin == "BTC":
                coin_dir = main_dir
            else:
                coin_dir = os.path.join(main_dir, coin)
            
            trainer_status_file = os.path.join(coin_dir, "trainer_status.json")
            
            if os.path.exists(trainer_status_file):
                try:
                    with open(trainer_status_file, 'r', encoding='utf-8') as f:
                        status = json.load(f)
                        # Check the "state" field (TRAINING or FINISHED)
                        state = str(status.get("state", "")).upper()
                        
                        if state == "FINISHED" or state == "COMPLETED":
                            trained_coins.append(coin)
                        elif state == "TRAINING":
                            training_coins.append(coin)
                        else:
                            # Check for alternative status fields
                            if status.get("trained", False) is True:
                                trained_coins.append(coin)
                            else:
                                last_run = status.get("last_run", status.get("last_training_time", status.get("started_at", "N/A")))
                                not_trained_coins.append(f"{coin} (State: {state}, Last: {last_run})")
                except Exception as e:
                    print(f"[TRAINING STATUS] Error reading {trainer_status_file}: {e}")
                    import traceback
                    traceback.print_exc()
                    not_trained_coins.append(f"{coin} (Error reading file)")
            else:
                not_trained_coins.append(f"{coin} (No status file)")
        
        if trained_coins:
            message += "✅ <b>Trained:</b>\n"
            for coin in trained_coins:
                message += f"  • {coin}\n"
            message += "\n"
        
        if training_coins:
            message += "🔄 <b>Training:</b>\n"
            for coin in training_coins:
                message += f"  • {coin}\n"
            message += "\n"
        
        if not_trained_coins:
            message += "❌ <b>Not Trained:</b>\n"
            for coin in not_trained_coins:
                message += f"  • {coin}\n"
        
        if not trained_coins and not not_trained_coins and not training_coins:
            message += "No training status found for any coins."
        
        return message
    
    def format_daily_report(self):
        """Format daily report message"""
        if not self.trader:
            return "❌ Error: PowerTrader not initialized. Check bot logs."
        
        account = self.trader.get_account()
        holdings = self.trader.get_holdings()
        
        if not account:
            return "📊 <b>Daily Report</b>\n\n❌ Error retrieving account data"
        
        # Calculate holdings value
        holdings_value = 0
        for holding in holdings[:15]:
            asset = holding['asset']
            quantity = holding['free'] + holding['locked']
            if quantity > 0.0001:
                try:
                    price = self.trader.get_price(asset)
                    if price:
                        holdings_value += quantity * price
                except:
                    pass
        
        total_value = account['balance'] + holdings_value
        percent_in_trade = (holdings_value / total_value * 100) if total_value > 0 else 0
        
        # Get recent trades
        orders = self.trader.get_orders(limit=20)
        today_orders = []
        today = datetime.now().date()
        
        for order in orders:
            try:
                order_time = datetime.fromtimestamp(order['time'] / 1000)
                if order_time.date() == today:
                    today_orders.append(order)
            except:
                pass
        
        buy_count = sum(1 for o in today_orders if o['side'] == 'BUY')
        sell_count = sum(1 for o in today_orders if o['side'] == 'SELL')
        
        # Determine if day is good or bad
        is_good_day = True
        if sell_count > buy_count * 2:  # More sells than buys
            is_good_day = False
        if percent_in_trade > 80:  # Too much in trades
            is_good_day = False
        
        status_icon = "✅" if is_good_day else "⚠️"
        status_text = "GOOD DAY" if is_good_day else "NEEDS ATTENTION"
        
        message = f"📊 <b>Daily Report - {datetime.now().strftime('%Y-%m-%d')}</b>\n\n"
        message += f"{status_icon} <b>Status: {status_text}</b>\n\n"
        message += f"💰 <b>Account Value:</b> {total_value:.2f} EUR\n"
        message += f"💵 Cash: {account['balance']:.2f} EUR\n"
        message += f"💎 In Trades: {holdings_value:.2f} EUR ({percent_in_trade:.1f}%)\n"
        message += f"💪 Buying Power: {account['buying_power']:.2f} EUR\n\n"
        message += f"📈 <b>Today's Activity:</b>\n"
        message += f"  🟢 Buys: {buy_count}\n"
        message += f"  🔴 Sells: {sell_count}\n"
        message += f"  📦 Active Holdings: {len(holdings)}\n\n"
        
        if is_good_day:
            message += "✅ System is running well!"
        else:
            message += "⚠️ Consider reviewing your trading strategy"
        
        return message
    
    def format_settings_view(self):
        """Format settings view"""
        settings = self._load_gui_settings()
        notif_settings = self._load_notification_settings()
        
        message = "🔧 <b>Settings</b>\n\n"
        message += "<b>Notification Settings:</b>\n"
        message += f"  Training Updates: {'✅ ON' if notif_settings.get('notify_training', True) else '❌ OFF'}\n"
        message += f"  Trade Notifications: {'✅ ON' if notif_settings.get('notify_trades', True) else '❌ OFF'}\n"
        message += f"  Profit/Loss Alerts: {'✅ ON' if notif_settings.get('notify_profit_loss', True) else '❌ OFF'}\n"
        message += f"  Daily Reports: {'✅ ON' if notif_settings.get('daily_report', True) else '❌ OFF'}\n\n"
        message += "<b>Trading Settings:</b>\n"
        message += f"  Trade Amount: {settings.get('fixed_trade_amount', 6)} EUR per trade\n"
        message += f"  Trade Allocation: {settings.get('trade_allocation_pct', 10)}%\n"
        message += f"  Min Trade Size: {settings.get('min_trade_size', 10)} EUR\n"
        
        return message
    
    def format_about(self):
        """Format about message"""
        message = "ℹ️ <b>About PowerTrader AI</b>\n\n"
        message += "A comprehensive trading bot management system\n"
        message += "for automated cryptocurrency trading.\n\n"
        message += "<b>Features:</b>\n"
        message += "• Automated trading with AI predictions\n"
        message += "• Neural network training\n"
        message += "• Real-time Telegram notifications\n"
        message += "• Interactive bot interface\n"
        message += "• Daily reports & profit tracking\n\n"
        message += "Supported by DogFun"
        return message
    
    def handle_callback(self, callback_data, message_id, user_id):
        """Handle callback queries"""
        try:
            if callback_data == "account":
                text = self.format_account_status()
                self.send_message(text, reply_markup=self.get_main_menu())
            elif callback_data == "profits":
                text = self.format_profits()
                self.send_message(text, reply_markup=self.get_main_menu())
            elif callback_data == "trades":
                text = self.format_current_trades()
                self.send_message(text, reply_markup=self.get_main_menu())
            elif callback_data == "training":
                text = self.format_training_status()
                self.send_message(text, reply_markup=self.get_main_menu())
            elif callback_data == "history":
                text = self.format_trade_history()
                self.send_message(text, reply_markup=self.get_main_menu())
            elif callback_data == "daily_report":
                text = self.format_daily_report()
                self.send_message(text, reply_markup=self.get_main_menu())
            elif callback_data == "settings":
                text = self.format_settings_view()
                self.send_message(text, reply_markup=self.get_settings_menu())
            elif callback_data == "back_to_menu":
                self.send_message("🤖 <b>Main Menu</b>\n\nSelect an option:", reply_markup=self.get_main_menu())
            elif callback_data == "toggle_training":
                notif_settings = self._load_notification_settings()
                notif_settings["notify_training"] = not notif_settings.get("notify_training", True)
                self._save_notification_settings(notif_settings)
                text = self.format_settings_view()
                self.send_message(text, reply_markup=self.get_settings_menu())
            elif callback_data == "toggle_trades":
                notif_settings = self._load_notification_settings()
                notif_settings["notify_trades"] = not notif_settings.get("notify_trades", True)
                self._save_notification_settings(notif_settings)
                text = self.format_settings_view()
                self.send_message(text, reply_markup=self.get_settings_menu())
            elif callback_data == "toggle_profit_loss":
                notif_settings = self._load_notification_settings()
                notif_settings["notify_profit_loss"] = not notif_settings.get("notify_profit_loss", True)
                self._save_notification_settings(notif_settings)
                text = self.format_settings_view()
                self.send_message(text, reply_markup=self.get_settings_menu())
            elif callback_data == "toggle_daily_report":
                notif_settings = self._load_notification_settings()
                notif_settings["daily_report"] = not notif_settings.get("daily_report", True)
                self._save_notification_settings(notif_settings)
                text = self.format_settings_view()
                self.send_message(text, reply_markup=self.get_settings_menu())
            elif callback_data == "set_min_purchase":
                self.waiting_for_input[user_id] = "min_purchase"
                self.send_message("💰 <b>Set Minimum Purchase Amount</b>\n\nPlease send the minimum purchase amount in EUR (e.g., 10, 25, 50):", reply_markup=None)
            elif callback_data == "set_trade_amount":
                self.waiting_for_input[user_id] = "trade_amount"
                self.send_message("💵 <b>Set Trade Amount</b>\n\nThis is the fixed amount (in EUR) the bot will use for each trade.\n\nPlease send the trade amount in EUR (e.g., 6, 10, 20):", reply_markup=None)
            elif callback_data == "set_allocation":
                self.waiting_for_input[user_id] = "allocation"
                self.send_message("📊 <b>Set Trade Allocation</b>\n\nPlease send the trade allocation percentage (e.g., 10, 20, 30):", reply_markup=None)
            elif callback_data == "about":
                text = self.format_about()
                logo_path = self.get_logo_path()
                if logo_path:
                    self.send_photo(logo_path, caption=text, reply_markup=self.get_main_menu())
                else:
                    self.send_message(text, reply_markup=self.get_main_menu())
            else:
                # Unknown callback - show menu
                self.send_message("Select an option:", reply_markup=self.get_main_menu())
        except Exception as e:
            print(f"Error handling callback {callback_data}: {e}")
            error_msg = f"❌ Error: {str(e)}\n\nShowing menu..."
            self.send_message(error_msg, reply_markup=self.get_main_menu())
    
    def handle_text_input(self, text, user_id):
        """Handle text input for settings"""
        if user_id not in self.waiting_for_input:
            return False
        
        input_type = self.waiting_for_input[user_id]
        
        try:
            if input_type == "trade_amount":
                value = float(text.strip())
                if value < 1:
                    self.send_message("❌ Trade amount must be at least 1 EUR")
                    return True
                settings = self._load_gui_settings()
                settings["fixed_trade_amount"] = value
                self._save_gui_settings(settings)
                del self.waiting_for_input[user_id]
                self.send_message(f"✅ Trade amount set to {value} EUR per trade", reply_markup=self.get_settings_menu())
                return True
            
            elif input_type == "min_purchase":
                value = float(text.strip())
                if value < 1:
                    self.send_message("❌ Minimum purchase amount must be at least 1 EUR")
                    return True
                settings = self._load_gui_settings()
                settings["min_trade_size"] = value
                self._save_gui_settings(settings)
                del self.waiting_for_input[user_id]
                self.send_message(f"✅ Minimum purchase amount set to {value} EUR", reply_markup=self.get_settings_menu())
                return True
            
            elif input_type == "allocation":
                value = float(text.strip())
                if value < 1 or value > 100:
                    self.send_message("❌ Trade allocation must be between 1% and 100%")
                    return True
                settings = self._load_gui_settings()
                settings["trade_allocation_pct"] = value
                self._save_gui_settings(settings)
                del self.waiting_for_input[user_id]
                self.send_message(f"✅ Trade allocation set to {value}%", reply_markup=self.get_settings_menu())
                return True
        except ValueError:
            self.send_message("❌ Invalid number. Please try again.")
            return True
        
        return False
    
    def format_trade_history(self):
        """Format trade history message - shows last 100 trades"""
        if not self.trader:
            return "❌ Error: PowerTrader not initialized. Check bot logs."
        
        orders = self.trader.get_orders(limit=100)
        if not orders:
            return "📜 <b>Trade History</b>\n\nNo recent trades"
        
        message = f"📜 <b>Trade History</b> (Last {len(orders)} trades)\n\n"
        # Show all orders (up to 100)
        for order in orders:
            symbol = self.trader._convert_symbol_from_binance(order['symbol'])
            side = order['side']
            status = order['status']
            quantity = float(order['executedQty'])
            price = float(order.get('price', 0)) or float(order.get('avgPrice', 0))
            
            side_icon = "🟢" if side == "BUY" else "🔴"
            message += f"{side_icon} <b>{side}</b> {symbol}: {quantity:.4f}"
            if price > 0:
                message += f" @ {price:.2f} EUR"
            message += f" ({status})\n"
        
        return message
    
    def handle_command(self, command, message_id):
        """Handle text commands"""
        command = command.lower().strip()
        
        if command in ["/start", "/menu", "start", "menu"]:
            logo_path = self.get_logo_path()
            welcome_text = "🤖 <b>PowerTrader AI Bot</b>\n\nWelcome! Use the menu below to interact.\n\nCommands:\n/start or /menu - Show this menu\n/about - About information\n/daily - Daily report\n\nOr click the buttons below:"
            if logo_path:
                self.send_photo(logo_path, caption=welcome_text, reply_markup=self.get_main_menu())
            else:
                self.send_message(welcome_text, reply_markup=self.get_main_menu())
        elif command == "/about" or command == "about":
            text = self.format_about()
            logo_path = self.get_logo_path()
            if logo_path:
                self.send_photo(logo_path, caption=text, reply_markup=self.get_main_menu())
            else:
                self.send_message(text, reply_markup=self.get_main_menu())
        elif command == "/daily" or command == "daily":
            text = self.format_daily_report()
            self.send_message(text, reply_markup=self.get_main_menu())
        elif command.startswith("/"):
            # Unknown command - show help
            help_text = "❓ <b>Unknown Command</b>\n\nAvailable commands:\n/start - Show main menu\n/menu - Show main menu\n/about - About information\n/daily - Daily report\n\nOr use the buttons below:"
            self.send_message(help_text, reply_markup=self.get_main_menu())
        else:
            # Any other text - show menu
            self.send_message("🤖 <b>PowerTrader AI Bot</b>\n\nSelect an option from the menu below:", reply_markup=self.get_main_menu())
    
    def _get_cached_data(self, key):
        """Get cached data if still valid"""
        if key in self._cache and key in self._last_cache_time:
            if time.time() - self._last_cache_time[key] < self._cache_timeout:
                return self._cache[key]
        return None
    
    def _set_cached_data(self, key, value):
        """Cache data with timestamp"""
        self._cache[key] = value
        self._last_cache_time[key] = time.time()
    
    def process_updates(self):
        """Process incoming updates - optimized for speed"""
        if not self.bot_token:
            print("[UPDATE ERROR] Bot token not loaded. Check telegram_token.txt")
            sys.stdout.flush()
            return
        
        # Clean token one more time before use
        self.bot_token = self._clean_token(self.bot_token)
        
        # Validate token format (should be numbers:letters)
        if ':' not in self.bot_token or len(self.bot_token) < 20:
            print(f"[UPDATE ERROR] Invalid bot token format. Token length: {len(self.bot_token)}")
            if len(self.bot_token) > 0:
                print(f"[UPDATE ERROR] Token preview: {repr(self.bot_token[:30])}")
            sys.stdout.flush()
            return
        
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 2  # Reduced from 10 to 2 seconds
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)  # Reduced from 15 to 5
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_update_id = update["update_id"]
                    
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        callback_data = callback["data"]
                        message_id = callback["message"]["message_id"]
                        user_id = str(callback["from"]["id"])
                        
                        # Answer callback immediately (don't wait)
                        answer_url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
                        try:
                            requests.post(answer_url, json={"callback_query_id": callback["id"]}, timeout=2)
                        except:
                            pass  # Don't block on answer
                        
                        # Handle callback in background
                        self.handle_callback(callback_data, message_id, user_id)
                    
                    elif "message" in update:
                        message = update["message"]
                        # Only process messages from the configured chat_id
                        chat_id_from_msg = str(message.get("chat", {}).get("id", ""))
                        if chat_id_from_msg != str(self.chat_id):
                            continue  # Skip logging for ignored messages
                        
                        user_id = str(message.get("from", {}).get("id", ""))
                        
                        if "text" in message:
                            text = message["text"].strip()
                            message_id = message["message_id"]
                            
                            # Check if user is waiting for input
                            if self.handle_text_input(text, user_id):
                                continue
                            
                            self.handle_command(text, message_id)
                        elif "photo" in message:
                            # Handle photo messages - show menu
                            self.send_message("🤖 <b>PowerTrader AI Bot</b>\n\nSelect an option:", reply_markup=self.get_main_menu())
        except requests.exceptions.RequestException as e:
            # Don't spam errors for network issues (404 is normal when no updates)
            if "404" not in str(e):
                print(f"[UPDATE] Error processing updates: {e}")
            sys.stdout.flush()
        except Exception as e:
            print(f"[UPDATE ERROR] Unexpected error processing updates: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
    
    def check_and_send_daily_report(self):
        """Check if it's time to send daily report"""
        notif_settings = self._load_notification_settings()
        if not notif_settings.get("daily_report", True):
            return
        
        now = datetime.now()
        today = now.date()
        
        # Check if we already sent today's report
        if self.last_daily_report_date == today:
            return
        
        # Check if it's time to send (default 9 AM)
        report_time = notif_settings.get("daily_report_time", "09:00")
        try:
            hour, minute = map(int, report_time.split(":"))
            if now.hour == hour and now.minute >= minute:
                if self.last_daily_report_date != today:
                    text = self.format_daily_report()
                    self.send_message(text, reply_markup=self.get_main_menu())
                    self.last_daily_report_date = today
        except:
            pass
    
    def run(self):
        """Main bot loop - optimized for speed"""
        print("=" * 60)
        print("Telegram bot starting...")
        print("=" * 60)
        
        if not self.bot_token:
            print("[BOT ERROR] Cannot start: Bot token is missing!")
            print(f"[BOT] Looking for token in: {os.path.join(self.base_dir, 'telegram_token.txt')}")
            return
        
        if not self.chat_id:
            print("[BOT WARNING] Chat ID not loaded. Bot may not respond to messages.")
        
        print(f"[BOT] Token loaded: {self.bot_token[:10]}...{self.bot_token[-5:]} (length: {len(self.bot_token)})")
        print(f"[BOT] Chat ID: {self.chat_id}")
        print("[BOT] Bot is running. Send /start to your bot to test.")
        print("=" * 60)
        
        last_daily_check = 0
        error_count = 0
        loop_count = 0
        
        while self.running:
            try:
                self.process_updates()
                error_count = 0  # Reset on success
                loop_count += 1
                
                # Print status every 100 loops (about every 50 seconds)
                if loop_count % 100 == 0:
                    print(f"[BOT] Still running... (processed {loop_count} loops)")
                
                # Only check daily report every 60 seconds (not every loop)
                now = time.time()
                if now - last_daily_check > 60:
                    self.check_and_send_daily_report()
                    last_daily_check = now
                time.sleep(0.5)  # Reduced from 1 to 0.5 seconds
            except KeyboardInterrupt:
                print("\n[BOT] Shutting down...")
                self.running = False
                break
            except Exception as e:
                error_count += 1
                print(f"[BOT ERROR] Error in bot loop: {e}")
                if error_count > 10:
                    print("[BOT ERROR] Too many errors, stopping bot")
                    break
                time.sleep(2)  # Reduced from 5 to 2 seconds

if __name__ == "__main__":
    # Wrap everything in try-except to catch ANY error
    try:
        print("\n[STEP 2] Creating TelegramBot instance...", flush=True)
        sys.stdout.flush()
        bot = TelegramBot()
        print("[MAIN] ✓ Bot initialized successfully", flush=True)
        sys.stdout.flush()
        
        print("\n[STEP 3] Starting bot run loop...", flush=True)
        sys.stdout.flush()
        bot.run()
    except KeyboardInterrupt:
        print("\n[MAIN] Bot stopped by user (Ctrl+C)", flush=True)
        sys.stdout.flush()
    except SystemExit as e:
        print(f"\n[MAIN] SystemExit: {e}", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"\n[MAIN ERROR] ✗ Failed to start bot: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        print("\nPress Enter to exit...", flush=True)
        try:
            input()
        except:
            pass
    finally:
        print("\n[MAIN] Script ending...", flush=True)
        sys.stdout.flush()
