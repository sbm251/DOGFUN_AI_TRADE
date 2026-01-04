import os
import json
import time
import hmac
import hashlib
import requests
from binance.client import Client
from telegram_notifications import notify_trade_executed

# Read API keys from files
def get_api_credentials():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "binance_key.txt")
    secret_path = os.path.join(base_dir, "binance_secret.txt")
    
    api_key = ""
    api_secret = ""
    
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            api_key = f.read().strip()
    
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            api_secret = f.read().strip()
    
    return api_key, api_secret

API_KEY, API_SECRET = get_api_credentials()

class PowerTrader:
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        self.base_currency = "EUR"
        self._load_settings()
    
    def _load_settings(self):
        settings_path = os.path.join(os.path.dirname(__file__), "gui_settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    self.trade_allocation_pct = settings.get("trade_allocation_pct", 10)
                    self.min_trade_size = settings.get("min_trade_size", 10)
                    self.fixed_trade_amount = settings.get("fixed_trade_amount", 6)  # Default 6 EUR per trade
            except:
                self.trade_allocation_pct = 10
                self.min_trade_size = 10
                self.fixed_trade_amount = 6
        else:
            self.trade_allocation_pct = 10
            self.min_trade_size = 10
            self.fixed_trade_amount = 6
    
    def _get_server_time(self):
        """Get Binance server time"""
        url = "https://api.binance.com/api/v3/time"
        response = requests.get(url, timeout=5)
        return response.json()['serverTime']
    
    def _sync_timestamp(self):
        """Synchronize timestamp with Binance server - use manual approach for reliability"""
        try:
            # Get server time directly from API
            server_time = self._get_server_time()
            local_time = int(time.time() * 1000)
            time_diff = server_time - local_time
            self.client.timestamp_adjustment = time_diff
        except Exception as e:
            # Fallback: try using client method
            try:
                server_time = self.client.get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = server_time['serverTime'] - local_time
                self.client.timestamp_adjustment = time_diff
            except Exception as e2:
                print(f"Error syncing timestamp: {e2}")
    
    def _convert_symbol_to_binance(self, symbol):
        """Convert symbol format to Binance format (e.g., BTC -> BTCEUR)"""
        return f"{symbol}{self.base_currency}"
    
    def _convert_symbol_from_binance(self, binance_symbol):
        """Convert Binance symbol format to our format (e.g., BTCEUR -> BTC)"""
        if binance_symbol.endswith(self.base_currency):
            return binance_symbol[:-len(self.base_currency)]
        return binance_symbol
    
    def get_account(self):
        """Get account information using manual signed request for better timestamp control"""
        try:
            # Get server time and create signed request manually (like test_api.py)
            server_time = self._get_server_time()
            
            # Prepare query string
            query_string = f"timestamp={server_time}&recvWindow=60000"
            
            # Create signature
            signature = hmac.new(
                API_SECRET.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Full query with signature
            full_query = f"{query_string}&signature={signature}"
            
            # Make request
            url = f"https://api.binance.com/api/v3/account?{full_query}"
            headers = {
                "X-MBX-APIKEY": API_KEY
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            account = response.json()
            
            # Find EUR balance
            eur_balance = 0
            for asset in account['balances']:
                if asset['asset'] == self.base_currency:
                    eur_balance = float(asset['free'])
                    break
            
            buying_power = eur_balance * (self.trade_allocation_pct / 100)
            
            return {
                'balance': eur_balance,
                'buying_power': buying_power,
                'trade_allocation_pct': self.trade_allocation_pct,
                'min_trade_size': self.min_trade_size
            }
        except Exception as e:
            print(f"Error getting account: {e}")
            return None
    
    def get_holdings(self):
        """Get current holdings (excluding base currency) using manual signed request"""
        try:
            # Get server time and create signed request manually (like test_api.py)
            server_time = self._get_server_time()
            
            # Prepare query string
            query_string = f"timestamp={server_time}&recvWindow=60000"
            
            # Create signature
            signature = hmac.new(
                API_SECRET.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Full query with signature
            full_query = f"{query_string}&signature={signature}"
            
            # Make request
            url = f"https://api.binance.com/api/v3/account?{full_query}"
            headers = {
                "X-MBX-APIKEY": API_KEY
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            account = response.json()
            
            holdings = []
            for asset in account['balances']:
                if float(asset['free']) > 0 and asset['asset'] != self.base_currency:
                    holdings.append({
                        'asset': asset['asset'],
                        'free': float(asset['free']),
                        'locked': float(asset['locked'])
                    })
            
            return holdings
        except Exception as e:
            print(f"Error getting holdings: {e}")
            return []
    
    def get_price(self, symbol):
        """Get current price for a symbol"""
        try:
            binance_symbol = self._convert_symbol_to_binance(symbol)
            if binance_symbol == "EUR-USD":
                return None
            ticker = self.client.get_symbol_ticker(symbol=binance_symbol)
            return float(ticker['price'])
        except Exception as e:
            # Don't print errors for invalid symbols (some assets don't have EUR pairs)
            # Only print if it's not an "Invalid symbol" error
            error_str = str(e)
            if "Invalid symbol" not in error_str and "-1121" not in error_str:
                print(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_trading_pairs(self):
        """Get available trading pairs with base currency"""
        try:
            exchange_info = self.client.get_exchange_info()
            pairs = []
            for symbol_info in exchange_info['symbols']:
                if symbol_info['quoteAsset'] == self.base_currency and symbol_info['status'] == 'TRADING':
                    pairs.append(symbol_info['baseAsset'])
            return pairs
        except Exception as e:
            print(f"Error getting trading pairs: {e}")
            return []
    
    def _get_lot_size_filter(self, binance_symbol):
        """Get LOT_SIZE filter (stepSize) for a symbol to round quantity correctly"""
        try:
            exchange_info = self.client.get_exchange_info()
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info['symbol'] == binance_symbol:
                    for filt in symbol_info.get('filters', []):
                        if filt.get('filterType') == 'LOT_SIZE':
                            step_size = float(filt.get('stepSize', '1.0'))
                            min_qty = float(filt.get('minQty', '0'))
                            max_qty = float(filt.get('maxQty', '0'))
                            return step_size, min_qty, max_qty
        except Exception as e:
            print(f"Error getting LOT_SIZE filter: {e}")
        # Default: no step size restriction (use 8 decimals)
        return None, 0, 0
    
    def _get_notional_filter(self, binance_symbol):
        """Get NOTIONAL filter (minimum order value) for a symbol"""
        try:
            exchange_info = self.client.get_exchange_info()
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info['symbol'] == binance_symbol:
                    for filt in symbol_info.get('filters', []):
                        if filt.get('filterType') == 'NOTIONAL':
                            min_notional = float(filt.get('minNotional', '0'))
                            return min_notional
        except Exception as e:
            print(f"Error getting NOTIONAL filter: {e}")
        # Default: assume 5 EUR minimum (conservative default)
        return 5.0
    
    def _round_quantity(self, quantity, step_size):
        """Round quantity to match Binance's step size requirement"""
        if step_size is None or step_size <= 0:
            # Default: round to 8 decimals
            return round(quantity, 8)
        # Round down to nearest step
        return (quantity // step_size) * step_size
    
    def place_buy_order(self, symbol, quantity=None, price=None):
        """Place a buy order - returns order dict on success, raises exception on error"""
        try:
            server_time = self._get_server_time()
            binance_symbol = self._convert_symbol_to_binance(symbol)
            
            if quantity is None:
                account = self.get_account()
                if account and account['buying_power'] >= self.min_trade_size:
                    if price:
                        quantity = account['buying_power'] / price
                    else:
                        current_price = self.get_price(symbol)
                        if current_price:
                            quantity = account['buying_power'] / current_price
            
            if not quantity or quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}")
            
            # Get current price to check notional value
            current_price = price or self.get_price(symbol)
            if not current_price or current_price <= 0:
                raise ValueError(f"Could not get current price for {symbol}")
            
            # Get NOTIONAL filter and validate order value
            min_notional = self._get_notional_filter(binance_symbol)
            notional_value = quantity * current_price
            
            if notional_value < min_notional:
                raise ValueError(
                    f"Order value {notional_value:.2f} EUR is below minimum notional {min_notional:.2f} EUR. "
                    f"Minimum order amount: {min_notional:.2f} EUR"
                )
            
            # Get LOT_SIZE filter and round quantity
            step_size, min_qty, max_qty = self._get_lot_size_filter(binance_symbol)
            quantity = self._round_quantity(quantity, step_size)
            
            # Re-check notional after rounding (in case rounding reduced the value)
            notional_value = quantity * current_price
            if notional_value < min_notional:
                # Try to increase quantity to meet minimum notional
                min_quantity = min_notional / current_price
                # Round up to next step
                if step_size and step_size > 0:
                    min_quantity = ((min_quantity // step_size) + 1) * step_size
                quantity = min_quantity
                notional_value = quantity * current_price
            
            # Check min/max quantity
            if min_qty > 0 and quantity < min_qty:
                raise ValueError(f"Quantity {quantity} is below minimum {min_qty}")
            if max_qty > 0 and quantity > max_qty:
                raise ValueError(f"Quantity {quantity} exceeds maximum {max_qty}")
            
            # Format quantity - use appropriate decimal places based on step size
            if step_size and step_size >= 1.0:
                qty_str = f"{int(quantity)}"  # Whole numbers
            elif step_size and step_size >= 0.1:
                qty_str = f"{quantity:.1f}"  # 1 decimal
            elif step_size and step_size >= 0.01:
                qty_str = f"{quantity:.2f}"  # 2 decimals
            else:
                qty_str = f"{quantity:.8f}"  # 8 decimals (default)
            
            # Use manual signed request for better error handling (like get_account)
            params = {
                "symbol": binance_symbol,
                "side": "BUY",
                "type": "MARKET",
                "quantity": qty_str,
                "timestamp": server_time,
                "recvWindow": 60000
            }
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                API_SECRET.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            full_url = f"https://api.binance.com/api/v3/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": API_KEY}
            
            response = requests.post(full_url, headers=headers, timeout=10)
            response.raise_for_status()
            order = response.json()
            
            # Send Telegram notification
            current_price = price or self.get_price(symbol)
            notify_trade_executed("BUY", symbol, quantity, current_price)
            
            return order
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e}"
            try:
                error_data = e.response.json()
                error_msg = f"Binance API Error: {error_data.get('msg', str(e))} (code: {error_data.get('code', 'unknown')})"
            except:
                pass
            print(f"Error placing buy order: {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error placing buy order: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e
    
    def place_sell_order(self, symbol, quantity):
        """Place a sell order - returns order dict on success, raises exception on error"""
        try:
            server_time = self._get_server_time()
            binance_symbol = self._convert_symbol_to_binance(symbol)
            
            if not quantity or quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}")
            
            # Get current price to check notional value
            current_price = self.get_price(symbol)
            if not current_price or current_price <= 0:
                raise ValueError(f"Could not get current price for {symbol}")
            
            # Get NOTIONAL filter and validate order value
            min_notional = self._get_notional_filter(binance_symbol)
            notional_value = quantity * current_price
            
            if notional_value < min_notional:
                raise ValueError(
                    f"Order value {notional_value:.2f} EUR is below minimum notional {min_notional:.2f} EUR. "
                    f"Minimum order amount: {min_notional:.2f} EUR"
                )
            
            # Get LOT_SIZE filter and round quantity
            step_size, min_qty, max_qty = self._get_lot_size_filter(binance_symbol)
            quantity = self._round_quantity(quantity, step_size)
            
            # Re-check notional after rounding (in case rounding reduced the value)
            notional_value = quantity * current_price
            if notional_value < min_notional:
                # Try to increase quantity to meet minimum notional
                min_quantity = min_notional / current_price
                # Round up to next step
                if step_size and step_size > 0:
                    min_quantity = ((min_quantity // step_size) + 1) * step_size
                quantity = min_quantity
                notional_value = quantity * current_price
            
            # Check min/max quantity
            if min_qty > 0 and quantity < min_qty:
                raise ValueError(f"Quantity {quantity} is below minimum {min_qty}")
            if max_qty > 0 and quantity > max_qty:
                raise ValueError(f"Quantity {quantity} exceeds maximum {max_qty}")
            
            # Format quantity - use appropriate decimal places based on step size
            if step_size and step_size >= 1.0:
                qty_str = f"{int(quantity)}"  # Whole numbers
            elif step_size and step_size >= 0.1:
                qty_str = f"{quantity:.1f}"  # 1 decimal
            elif step_size and step_size >= 0.01:
                qty_str = f"{quantity:.2f}"  # 2 decimals
            else:
                qty_str = f"{quantity:.8f}"  # 8 decimals (default)
            
            # Use manual signed request for better error handling (like get_account)
            params = {
                "symbol": binance_symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": qty_str,
                "timestamp": server_time,
                "recvWindow": 60000
            }
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(
                API_SECRET.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            full_url = f"https://api.binance.com/api/v3/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": API_KEY}
            
            response = requests.post(full_url, headers=headers, timeout=10)
            response.raise_for_status()
            order = response.json()
            
            # Send Telegram notification
            price = self.get_price(symbol)
            notify_trade_executed("SELL", symbol, quantity, price)
            
            return order
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e}"
            try:
                error_data = e.response.json()
                error_msg = f"Binance API Error: {error_data.get('msg', str(e))} (code: {error_data.get('code', 'unknown')})"
            except:
                pass
            print(f"Error placing sell order: {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Error placing sell order: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) from e
    
    def get_orders(self, symbol=None, limit=10):
        """Get recent orders - returns up to limit most recent orders across all pairs"""
        try:
            self._sync_timestamp()
            if symbol:
                binance_symbol = self._convert_symbol_to_binance(symbol)
                orders = self.client.get_all_orders(symbol=binance_symbol, limit=min(limit, 1000), recvWindow=60000)
            else:
                orders = []
                # Get orders from all trading pairs to find the most recent ones
                pairs = self.get_trading_pairs()
                
                # Calculate how many orders to get per pair to ensure we have enough for top N
                # If we want 100 total and have 10 pairs, get ~15-20 per pair to have buffer
                num_pairs = len(pairs) if pairs else 1
                per_pair_limit = max(20, (limit * 2) // num_pairs)  # Get more per pair to ensure we have enough
                per_pair_limit = min(per_pair_limit, 100)  # But cap at 100 per pair (Binance API limit per symbol)
                
                for pair in pairs:
                    binance_symbol = self._convert_symbol_to_binance(pair)
                    try:
                        pair_orders = self.client.get_all_orders(symbol=binance_symbol, limit=per_pair_limit, recvWindow=60000)
                        if pair_orders:
                            orders.extend(pair_orders)
                    except Exception as e:
                        # Skip pairs that fail (might not have orders)
                        continue
                
                # Sort by time (most recent first) and limit to requested number
                if orders:
                    # Sort by time field (milliseconds since epoch)
                    orders.sort(key=lambda x: int(x.get('time', x.get('updateTime', 0))), reverse=True)
                    orders = orders[:limit]
            
            return orders
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

if __name__ == "__main__":
    import sys
    
    # Get hub_data directory from environment or default
    hub_dir = os.environ.get("POWERTRADER_HUB_DIR") or os.path.join(os.path.dirname(__file__), "hub_data")
    os.makedirs(hub_dir, exist_ok=True)
    
    trader_status_path = os.path.join(hub_dir, "trader_status.json")
    trade_history_path = os.path.join(hub_dir, "trade_history.jsonl")
    account_value_history_path = os.path.join(hub_dir, "account_value_history.jsonl")
    
    trader = PowerTrader()
    
    print("[TRADER] Starting trading bot...")
    print(f"[TRADER] Hub directory: {hub_dir}")
    
    # Main trading loop
    last_status_write = 0
    status_write_interval = 2  # Write status every 2 seconds (faster updates)
    
    try:
        while True:
            try:
                # Get account info
                account = trader.get_account()
                
                # Get holdings
                holdings = trader.get_holdings()
                
                # Write status for GUI
                current_time = time.time()
                if current_time - last_status_write >= status_write_interval:
                    # Calculate total account value (EUR balance + holdings value)
                    total_account_value = 0.0
                    holdings_sell_value = 0.0
                    percent_in_trade = 0.0
                    
                    if account:
                        eur_balance = account.get('balance', 0.0)
                        total_account_value = eur_balance
                        
                        # Calculate holdings value
                        for holding in holdings:
                            asset = holding['asset']
                            quantity = holding['free'] + holding['locked']
                            try:
                                price = trader.get_price(asset)
                                if price and price > 0:
                                    holding_value = quantity * price
                                    holdings_sell_value += holding_value
                                    total_account_value += holding_value
                            except Exception:
                                pass
                        
                        # Calculate percent in trade
                        if total_account_value > 0:
                            percent_in_trade = (holdings_sell_value / total_account_value) * 100
                    
                    # Enhanced account info for GUI
                    enhanced_account = {
                        "balance": account.get('balance', 0.0) if account else 0.0,
                        "buying_power": account.get('buying_power', 0.0) if account else 0.0,
                        "total_account_value": total_account_value,
                        "holdings_sell_value": holdings_sell_value,
                        "percent_in_trade": percent_in_trade
                    }
                    
                    # Calculate positions from holdings and trade history
                    positions = {}
                    try:
                        # Read trade history to calculate average cost basis
                        buy_trades_by_coin = {}
                        if os.path.exists(trade_history_path):
                            with open(trade_history_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    try:
                                        trade = json.loads(line.strip())
                                        symbol = trade.get('symbol', '').upper().strip()
                                        side = trade.get('side', '').lower().strip()
                                        if side == 'buy' and symbol:
                                            if symbol not in buy_trades_by_coin:
                                                buy_trades_by_coin[symbol] = []
                                            buy_trades_by_coin[symbol].append(trade)
                                    except Exception:
                                        pass
                        
                        # Build positions from holdings
                        for holding in holdings:
                            asset = holding['asset']
                            if asset == 'EUR':
                                continue
                            
                            quantity = holding['free'] + holding['locked']
                            if quantity <= 0.0001:  # Skip dust
                                continue
                            
                            try:
                                current_price = trader.get_price(asset)
                                if not current_price or current_price <= 0:
                                    continue
                                
                                # Calculate average cost basis from buy trades
                                avg_cost_basis = current_price  # Default to current price
                                total_cost = 0.0
                                total_qty = 0.0
                                
                                if asset in buy_trades_by_coin:
                                    for trade in buy_trades_by_coin[asset]:
                                        qty = float(trade.get('quantity', 0))
                                        price = float(trade.get('price', 0))
                                        if qty > 0 and price > 0:
                                            total_cost += (qty * price)
                                            total_qty += qty
                                    
                                    if total_qty > 0:
                                        avg_cost_basis = total_cost / total_qty
                                
                                # Calculate position value and P/L
                                position_value = quantity * current_price
                                unrealized_pnl = (current_price - avg_cost_basis) * quantity
                                unrealized_pnl_pct = ((current_price - avg_cost_basis) / avg_cost_basis * 100) if avg_cost_basis > 0 else 0.0
                                
                                positions[asset] = {
                                    "quantity": round(quantity, 8),
                                    "value_usd": round(position_value, 2),  # GUI expects USD but we use EUR
                                    "avg_cost_basis": round(avg_cost_basis, 8),
                                    "current_buy_price": round(current_price, 8),
                                    "gain_loss_pct_buy": round(unrealized_pnl_pct, 2),
                                    "current_sell_price": round(current_price, 8),
                                    "gain_loss_pct_sell": round(unrealized_pnl_pct, 2),
                                    "dca_triggered_stages": 0,
                                    "next_dca_display": "",
                                    "trail_line": 0.0
                                }
                            except Exception as e:
                                # Skip if price fetch fails
                                pass
                    except Exception as e:
                        print(f"[TRADER] Error calculating positions: {e}")
                    
                    status = {
                        "timestamp": current_time,
                        "account": enhanced_account,
                        "holdings": holdings,
                        "positions": positions,
                        "status": "running"
                    }
                    
                    try:
                        with open(trader_status_path, 'w', encoding='utf-8') as f:
                            json.dump(status, f, indent=2)
                        last_status_write = current_time
                        
                        # Write account value history for the chart (both total and holdings)
                        try:
                            account_value_entry = {
                                "ts": current_time,
                                "total_account_value": total_account_value,
                                "holdings_sell_value": holdings_sell_value
                            }
                            with open(account_value_history_path, 'a', encoding='utf-8') as f:
                                f.write(json.dumps(account_value_entry) + '\n')
                        except Exception as e:
                            print(f"[TRADER] Error writing account value history: {e}")
                    except Exception as e:
                        print(f"[TRADER] Error writing status: {e}")
                
                # Trading logic: Read signals and execute trades
                try:
                    # Get configured coins from settings
                    settings_path = os.path.join(os.path.dirname(__file__), "gui_settings.json")
                    main_neural_dir = r"C:\PowerTrader_AI"  # Default
                    coins = []
                    
                    if os.path.exists(settings_path):
                        try:
                            with open(settings_path, 'r', encoding='utf-8') as f:
                                settings = json.load(f)
                                main_neural_dir = settings.get("main_neural_dir", main_neural_dir)
                                coins = [c.upper().strip() for c in settings.get("coins", [])]
                                
                                # Filter out ignored coins
                                ignored_coins = settings.get("ignored_coins", [])
                                if isinstance(ignored_coins, list):
                                    ignored_set = {str(c).strip().upper() for c in ignored_coins if str(c).strip()}
                                    coins = [c for c in coins if c not in ignored_set]
                        except Exception:
                            pass
                    
                    # Get trade_start_level setting (default: 2, previously defaulted to 3)
                    # Reload each loop to get latest value
                    trade_start_level = 2  # Default
                    if os.path.exists(settings_path):
                        try:
                            with open(settings_path, 'r', encoding='utf-8') as f:
                                settings = json.load(f)
                                trade_start_level = int(settings.get("trade_start_level", 2))
                        except Exception:
                            pass
                    
                    # Process each coin
                    for coin in coins:
                        if not coin or coin == "EUR":
                            continue
                        
                        # Get coin folder (BTC uses main dir, others use subfolder)
                        if coin == "BTC":
                            coin_folder = main_neural_dir
                        else:
                            coin_folder = os.path.join(main_neural_dir, coin)
                        
                        if not os.path.isdir(coin_folder):
                            continue
                        
                        # Read signals
                        long_signal = 0
                        short_signal = 0
                        
                        long_signal_path = os.path.join(coin_folder, "long_dca_signal.txt")
                        short_signal_path = os.path.join(coin_folder, "short_dca_signal.txt")
                        
                        try:
                            if os.path.exists(long_signal_path):
                                with open(long_signal_path, 'r', encoding='utf-8') as f:
                                    long_signal = int(float(f.read().strip() or 0))
                        except Exception:
                            pass
                        
                        try:
                            if os.path.exists(short_signal_path):
                                with open(short_signal_path, 'r', encoding='utf-8') as f:
                                    short_signal = int(float(f.read().strip() or 0))
                        except Exception:
                            pass
                        
                        # Only trade if there's an active signal
                        if long_signal == 0 and short_signal == 0:
                            continue
                        
                        # Get current price
                        current_price = trader.get_price(coin)
                        if not current_price or current_price <= 0:
                            continue
                        
                        # Read neural levels
                        low_bound_path = os.path.join(coin_folder, "low_bound_prices.html")
                        high_bound_path = os.path.join(coin_folder, "high_bound_prices.html")
                        
                        low_levels = []
                        high_levels = []
                        
                        # Parse low_bound_prices.html (same format as GUI uses)
                        if os.path.exists(low_bound_path):
                            try:
                                with open(low_bound_path, 'r', encoding='utf-8') as f:
                                    raw = f.read().strip()
                                raw = raw.replace(",", " ").replace("[", " ").replace("]", " ").replace("'", " ")
                                for tok in raw.split():
                                    try:
                                        v = float(tok)
                                        if v > 0 and v < 9e15:  # Filter sentinel values
                                            low_levels.append(v)
                                    except Exception:
                                        pass
                                low_levels.sort(reverse=True)  # Highest first
                            except Exception:
                                pass
                        
                        # Parse high_bound_prices.html
                        if os.path.exists(high_bound_path):
                            try:
                                with open(high_bound_path, 'r', encoding='utf-8') as f:
                                    raw = f.read().strip()
                                raw = raw.replace(",", " ").replace("[", " ").replace("]", " ").replace("'", " ")
                                for tok in raw.split():
                                    try:
                                        v = float(tok)
                                        if v > 0 and v < 9e15:  # Filter sentinel values
                                            high_levels.append(v)
                                    except Exception:
                                        pass
                                high_levels.sort()  # Lowest first
                            except Exception:
                                pass
                        
                        # Check if we should buy (LONG signal and price near a low level)
                        if long_signal > 0 and low_levels:
                            # Trade Start Level: Price must be below at least N blue lines before trade starts
                            # Count how many blue lines (low_levels) are above the current price
                            # low_levels are sorted reverse (highest first), so count levels > current_price
                            lines_above_price = sum(1 for level in low_levels if level > current_price)
                            
                            # Only proceed if price is below the required number of blue lines
                            if lines_above_price < trade_start_level:
                                continue  # Price not low enough yet, skip this coin
                            
                            # Dynamic tolerance based on signal strength: L:7 = 10%, L:6 = 7%, L:5 = 5%, L:4 = 4%, L:3 = 3%, L:2-1 = 2%
                            max_tolerance = min(10.0, 2.0 + (long_signal * 1.2))  # L:7 = 10.4% (capped at 10%), L:6 = 9.2%, etc.
                            
                            # Find the closest low level near current price (buy at support)
                            # Low levels are support levels - buy when price is within tolerance of any support level
                            for level in low_levels:
                                # Calculate distance from price to support level (absolute percentage)
                                if current_price <= level:
                                    # Price is at or below support
                                    price_diff_pct = abs((level - current_price) / current_price) * 100
                                else:
                                    # Price is above support
                                    price_diff_pct = abs((current_price - level) / level) * 100
                                
                                # Buy if price is within dynamic tolerance of the support level
                                if price_diff_pct <= max_tolerance:
                                    # Check if we already have this coin
                                    has_holding = any(h['asset'] == coin for h in holdings)
                                    
                                    # Use fixed trade amount (configurable via Telegram, default 6 EUR)
                                    # Reload settings to get latest fixed_trade_amount
                                    trader._load_settings()
                                    trade_amount = trader.fixed_trade_amount
                                    
                                    # Only buy if we don't already have it and have enough balance
                                    if not has_holding and account and account['balance'] >= trade_amount and trade_amount >= trader.min_trade_size:
                                        try:
                                            # Calculate quantity based on position size
                                            quantity = trade_amount / current_price
                                            order = trader.place_buy_order(coin, quantity=quantity)
                                            if order:
                                                # Write to trade history
                                                # Calculate average price from order response
                                                executed_qty = float(order.get('executedQty', 0))
                                                cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0) or order.get('cummulativeFilledQuoteQty', 0) or 0)
                                                if executed_qty > 0 and cummulative_quote_qty > 0:
                                                    avg_price = cummulative_quote_qty / executed_qty
                                                else:
                                                    # Fallback: try fills array or use current price
                                                    fills = order.get('fills', [])
                                                    if fills and len(fills) > 0:
                                                        total_cost = sum(float(f.get('price', 0)) * float(f.get('qty', 0)) for f in fills)
                                                        total_qty = sum(float(f.get('qty', 0)) for f in fills)
                                                        avg_price = (total_cost / total_qty) if total_qty > 0 else current_price
                                                    else:
                                                        avg_price = current_price
                                                
                                                trade_entry = {
                                                    "ts": time.time(),
                                                    "side": "buy",
                                                    "symbol": coin,
                                                    "quantity": executed_qty,
                                                    "price": avg_price,
                                                    "tag": "NEURAL"
                                                }
                                                try:
                                                    with open(trade_history_path, 'a', encoding='utf-8') as f:
                                                        f.write(json.dumps(trade_entry) + '\n')
                                                    print(f"[TRADER] BUY {coin} at {current_price:.4f} EUR (signal: L{long_signal}, level: {level:.4f}, diff: {price_diff_pct:.2f}%, size: {trade_amount:.2f} EUR, start_level: {trade_start_level})")
                                                except Exception:
                                                    pass
                                        except Exception as e:
                                            print(f"[TRADER] Error buying {coin}: {e}")
                                    break  # Only check the first (closest) level that matches
                        
                        # Check if we should sell (SHORT signal and price near a high level, or we have holdings)
                        if short_signal > 0 or any(h['asset'] == coin for h in holdings):
                            # If we have holdings, check for sell opportunities
                            coin_holding = next((h for h in holdings if h['asset'] == coin), None)
                            
                            if coin_holding and high_levels:
                                # Calculate average cost basis from trade history (for profit-taking calculations)
                                avg_cost = current_price  # Default to current price if no history
                                try:
                                    if os.path.exists(trade_history_path):
                                        with open(trade_history_path, 'r', encoding='utf-8') as f:
                                            trades = [json.loads(line.strip()) for line in f if line.strip()]
                                        buy_trades = [t for t in trades if t.get('symbol', '').upper() == coin and t.get('side', '').lower() == 'buy']
                                        if buy_trades:
                                            total_cost = sum(float(t.get('quantity', 0)) * float(t.get('price', 0)) for t in buy_trades)
                                            total_qty = sum(float(t.get('quantity', 0)) for t in buy_trades)
                                            if total_qty > 0:
                                                avg_cost = total_cost / total_qty
                                except Exception:
                                    pass
                                
                                # NO STOP-LOSS: Spot trading philosophy - hold through dips, add more via DCA if needed
                                # The DCA multiplier is large, so cost basis lowers significantly with each DCA
                                # User prefers to add more money to account rather than realize losses
                                
                                # Profit-taking: Take 50% profit at +5%, rest at resistance
                                current_profit_pct = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
                                if current_profit_pct >= 5.0:
                                    # Check if we already took partial profit (by checking trade history)
                                    try:
                                        already_took_profit = False
                                        if os.path.exists(trade_history_path):
                                            with open(trade_history_path, 'r', encoding='utf-8') as f:
                                                for line in f:
                                                    line = line.strip()
                                                    if line:
                                                        try:
                                                            trade = json.loads(line)
                                                            if (trade.get('symbol', '').upper() == coin and 
                                                                trade.get('tag', '') == 'PROFIT_TAKE'):
                                                                already_took_profit = True
                                                                break
                                                        except Exception:
                                                            pass
                                        if not already_took_profit:  # Haven't taken profit yet
                                                quantity = coin_holding['free'] * 0.5  # Sell 50%
                                                if quantity > 0:
                                                    order = trader.place_sell_order(coin, quantity)
                                                    if order:
                                                        # Calculate average price from order response
                                                        executed_qty = float(order.get('executedQty', 0) or quantity)
                                                        cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0) or order.get('cummulativeFilledQuoteQty', 0) or 0)
                                                        if executed_qty > 0 and cummulative_quote_qty > 0:
                                                            avg_price = cummulative_quote_qty / executed_qty
                                                        else:
                                                            # Fallback: try fills array or use current price
                                                            fills = order.get('fills', [])
                                                            if fills and len(fills) > 0:
                                                                total_cost = sum(float(f.get('price', 0)) * float(f.get('qty', 0)) for f in fills)
                                                                total_qty = sum(float(f.get('qty', 0)) for f in fills)
                                                                avg_price = (total_cost / total_qty) if total_qty > 0 else current_price
                                                            else:
                                                                avg_price = current_price
                                                        
                                                        trade_entry = {
                                                            "ts": time.time(),
                                                            "side": "sell",
                                                            "symbol": coin,
                                                            "quantity": executed_qty,
                                                            "price": avg_price,
                                                            "tag": "PROFIT_TAKE"
                                                        }
                                                        try:
                                                            with open(trade_history_path, 'a', encoding='utf-8') as f:
                                                                f.write(json.dumps(trade_entry) + '\n')
                                                            print(f"[TRADER] SELL 50% {coin} at {current_price:.4f} EUR (PROFIT-TAKE: +{current_profit_pct:.2f}%)")
                                                        except Exception:
                                                            pass
                                    except Exception:
                                        pass
                                
                                # Find the closest high level near current price (sell at resistance)
                                for level in reversed(high_levels):  # Check highest first
                                    if level <= current_price:
                                        # Price is at or above resistance - check if we should sell
                                        price_diff_pct = ((current_price - level) / level) * 100
                                        # Sell if price is within 2% above the level (at resistance)
                                        if price_diff_pct <= 2.0:
                                            try:
                                                quantity = coin_holding['free']  # Sell remaining position
                                                if quantity > 0:
                                                    order = trader.place_sell_order(coin, quantity)
                                                    if order:
                                                        # Calculate average price from order response
                                                        executed_qty = float(order.get('executedQty', 0) or quantity)
                                                        cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0) or order.get('cummulativeFilledQuoteQty', 0) or 0)
                                                        if executed_qty > 0 and cummulative_quote_qty > 0:
                                                            avg_price = cummulative_quote_qty / executed_qty
                                                        else:
                                                            # Fallback: try fills array or use current price
                                                            fills = order.get('fills', [])
                                                            if fills and len(fills) > 0:
                                                                total_cost = sum(float(f.get('price', 0)) * float(f.get('qty', 0)) for f in fills)
                                                                total_qty = sum(float(f.get('qty', 0)) for f in fills)
                                                                avg_price = (total_cost / total_qty) if total_qty > 0 else current_price
                                                            else:
                                                                avg_price = current_price
                                                        
                                                        # Write to trade history
                                                        trade_entry = {
                                                            "ts": time.time(),
                                                            "side": "sell",
                                                            "symbol": coin,
                                                            "quantity": executed_qty,
                                                            "price": avg_price,
                                                            "tag": "NEURAL"
                                                        }
                                                        try:
                                                            with open(trade_history_path, 'a', encoding='utf-8') as f:
                                                                f.write(json.dumps(trade_entry) + '\n')
                                                            print(f"[TRADER] SELL {coin} at {current_price:.4f} EUR (signal: S{short_signal})")
                                                        except Exception:
                                                            pass
                                            except Exception as e:
                                                print(f"[TRADER] Error selling {coin}: {e}")
                                        break  # Only check the first (closest) level
                
                except Exception as e:
                    print(f"[TRADER] Error in trading logic: {e}")
                    import traceback
                    traceback.print_exc()
                
                time.sleep(1)  # Check every 1 second (faster response to signals)
                
            except KeyboardInterrupt:
                print("\n[TRADER] Shutting down...")
                break
            except Exception as e:
                print(f"[TRADER] Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(2)  # Wait before retrying (reduced from 5 to 2 seconds)
                
    except Exception as e:
        print(f"[TRADER] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

