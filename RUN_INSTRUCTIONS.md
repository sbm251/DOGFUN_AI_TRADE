Disclaimer: Trading cryptocurrencies or financial instruments carries significant risk. This trading bot is provided for educational and informational purposes only. You use it at your own risk, and I assume no responsibility for any losses or damages.


================================================================================
                    POWERTRADER AI - USER GUIDE
================================================================================

Welcome to PowerTrader AI! This guide will help you set up and use the 
automated cryptocurrency trading bot.

================================================================================
                            TABLE OF CONTENTS
================================================================================

1. OVERVIEW
2. SYSTEM COMPONENTS
3. INITIAL SETUP
4. CONFIGURATION
5. USING THE GUI
6. USING TELEGRAM BOT
7. TRADING FEATURES
8. UNDERSTANDING CHARTS
9. TROUBLESHOOTING
10. IMPORTANT NOTES

================================================================================
                                1. OVERVIEW
================================================================================

PowerTrader AI is an automated cryptocurrency trading bot that uses neural 
networks to analyze market data and execute trades on Binance. The system 
consists of four main components:

- TRAINER: Trains neural networks for each cryptocurrency
- NEURAL RUNNER: Generates trading signals and price levels
- TRADER: Executes trades based on signals
- GUI: Visual interface for monitoring and control

================================================================================
                            2. SYSTEM COMPONENTS
================================================================================


Disclaimer: Trading cryptocurrencies or financial instruments carries significant risk. This trading bot is provided for educational and informational purposes only. You use it at your own risk, and I assume no responsibility for any losses or damages.

2.1 TRAINER (pt_hub_advanced.py)
   - Trains neural networks for each coin you want to trade
   - Must be run before trading can begin
   - Creates training data and neural network models
   - Status saved in trainer_status.json

2.2 NEURAL RUNNER (pt_thinker.py)
   - Analyzes market data in real-time
   - Generates buy/sell signals (LONG/SHORT)
   - Creates price boundary levels (neural lines on charts)
   - Writes signals to long_dca_signal.txt and short_dca_signal.txt
   - Must be running for the trader to work

2.3 TRADER (pt_trader.py)
   - Monitors signals from Neural Runner
   - Executes buy/sell orders on Binance
   - Manages positions and risk
   - Writes status to trader_status.json
   - Records trade history in trade_history.jsonl

2.4 GUI (pt_hub_advanced.py)
   - Main control interface
   - Start/stop all components
   - View account status and trades
   - Monitor charts and signals
   - Manual trading controls

2.5 TELEGRAM BOT (telegram_bot.py)
   - Receive notifications about trades
   - Check account status remotely
   - Control bot settings
   - View trade history

================================================================================
                              3. INITIAL SETUP
================================================================================

3.1 INSTALL DEPENDENCIES
   - Install Python 3.8 or higher
   - Run: pip install -r requirements.txt

3.2 BINANCE API SETUP
   - Create a Binance account
   - Generate API key and secret
   - Save API key to: binance_key.txt
   - Save API secret to: binance_secret.txt
   - IMPORTANT: Enable "Enable Spot & Margin Trading" in API settings
   - IMPORTANT: Do NOT enable "Enable Withdrawals" for security

3.3 TELEGRAM BOT SETUP (Optional)
   - Create a Telegram bot via @BotFather
   - Get your bot token
   - Save token to: telegram_token.txt
   - Get your chat ID (send message to bot, visit: 
     https://api.telegram.org/bot<TOKEN>/getUpdates)
   - Save chat ID to: telegram_chat_id.txt

3.4 CONFIGURE COINS
   - Edit gui_settings.json
   - Add coins to the "coins" array (e.g., ["BTC", "ETH", "DOGE"])
   - Set "main_neural_dir" to your desired data directory

================================================================================
                               4. CONFIGURATION
================================================================================

4.1 GUI SETTINGS (gui_settings.json)

   "main_neural_dir": "C:\\PowerTrader_AI"
      - Directory where neural data is stored
   
   "coins": ["BTC", "ETH", "DOGE"]
      - List of cryptocurrencies to trade
   
   "default_timeframe": "1hour"
      - Default chart timeframe
   
   "fixed_trade_amount": 6
      - Amount in EUR to use for each trade (default: 6 EUR)
      - Can be changed via GUI or Telegram
   
   "ui_refresh_seconds": 0.5
      - How often GUI updates (seconds)
   
   "chart_refresh_seconds": 5.0
      - How often charts update (seconds)
   
   "auto_start_scripts": true
      - Automatically start components when GUI opens

4.2 TRADING SETTINGS

   Fixed Trade Amount:
   - Each buy order uses this fixed amount (default: 6 EUR)
   - Change via GUI: Account section -> "Trade Amount" -> "Set"
   - Change via Telegram: Settings -> Trade Amount

   Position Sizing:
   - Based on signal strength (L:7 = 100%, L:6 = 86%, etc.)
   - Automatically calculated by trader

   Stop-Loss:
   - Automatic stop-loss at -5% loss
   - Sells 100% of position

   Profit-Taking:
   - Takes 50% profit at +5% gain
   - Only triggers once per position

================================================================================
                              5. USING THE GUI
================================================================================

5.1 STARTING THE GUI
   - Run: python pt_hub_advanced.py
   - The GUI will open with dark theme

5.2 MAIN SECTIONS

   ACCOUNT SECTION:
   - Total Account Value: Your total balance + holdings
   - Holdings Value: Current value of your cryptocurrency holdings
   - Buying Power: Available EUR for trading
   - Trade Amount: Fixed amount per trade (click "Set" to change)
   - Percent In Trade: Percentage of account in active positions
   - DCA Levels: Dollar-Cost Averaging levels based on account value

   CONTROLS SECTION:
   - Start All: Starts Neural Runner, then Trader (when ready)
   - Stop All: Stops all running components
   - Start Neural Runner: Starts only the Neural Runner
   - Start Trader: Starts only the Trader
   - Test Buy: Manual buy button (select coin from dropdown)
   - Sell All: Sells all holdings immediately
   - Sell Coin: Select coin and sell (prompts for amount)

   COIN STATUS:
   - Shows training status for each coin
   - "TRAINED" = Ready to trade
   - "NOT TRAINED" = Needs training first
   - Click coin name to view detailed chart

5.3 CHARTS

   ACCOUNT VALUE CHART:
   - Cyan line: Total Account Value (balance + holdings)
   - Orange line: Holdings Value (what you can sell)
   - Shows account value over time
   - Trade markers: Red dots (BUY), Green dots (SELL), Purple dots (DCA)

   COIN CHARTS:
   - Price chart with neural levels
   - Blue lines: LONG signals (buy levels)
   - Orange lines: SHORT signals (sell levels)
   - Numbers (0-7): Signal strength
   - Current price shown as horizontal line

5.4 CURRENT TRADES TABLE
   - Shows all active positions
   - Columns: Coin, Quantity, Value, Avg Cost, Ask/Bid Price, P/L, etc.
   - Updates automatically

================================================================================
                           6. USING TELEGRAM BOT
================================================================================

6.1 STARTING THE BOT
   - Run: python telegram_bot.py
   - Bot will respond to commands in your Telegram chat

6.2 AVAILABLE COMMANDS

   /start - Start the bot and show main menu
   
   /status - View account status
      - Total account value
      - Holdings value
      - Buying power
      - Active positions
   
   /settings - View and change settings
      - Trade amount
      - Trading pairs
      - Other settings
   
   /trades - View recent trade history
      - Shows last 100 trades
      - Buy/sell details
      - Profit/loss information
   
   /help - Show help message

6.3 BUTTONS

   💵 Trade Amount - Change fixed trade amount
   📊 Account Status - View account details
   ⚙️ Settings - View settings
   📈 Trades - View trade history

================================================================================
                            7. TRADING FEATURES
================================================================================

7.1 AUTOMATIC TRADING

   BUY CONDITIONS:
   - LONG signal > 0 (from Neural Runner)
   - No existing position for that coin
   - Current price within tolerance of a LOW level (blue line)
   - Trade amount >= minimum (6 EUR default)
   - Account has sufficient buying power

   SELL CONDITIONS:
   - SHORT signal > 0 OR has existing position
   - Current price within 2% above a HIGH level (orange line)
   - Stop-loss: -5% loss (sells 100%)
   - Profit-taking: +5% gain (sells 50%, once per position)

7.2 MANUAL TRADING

   TEST BUY:
   - Select coin from dropdown
   - Click "Test Buy"
   - Enter amount (default: uses fixed trade amount)
   - Order executes immediately at market price

   SELL COIN:
   - Select coin from dropdown
   - Click "Sell Coin"
   - Enter amount to sell:
     * Percentage: "50%" (sells 50% of holdings)
     * Quantity: "10.5" (sells 10.5 coins)
     * EUR amount: "5 EUR" (sells coins worth 5 EUR)

   SELL ALL:
   - Sells all holdings immediately
   - Market orders for all coins

7.3 SIGNAL STRENGTH

   LONG Signals (L:0 to L:7):
   - L:7 = Strongest buy signal (100% position size)
   - L:6 = 86% position size
   - L:5 = 71% position size
   - L:4 = 57% position size
   - L:3 = 43% position size
   - L:2 = 29% position size
   - L:1 = 14% position size
   - L:0 = Weakest signal

   SHORT Signals (S:0 to S:7):
   - Similar scale for sell signals
   - Higher number = stronger signal

================================================================================
                          8. UNDERSTANDING CHARTS
================================================================================

8.1 NEURAL LEVELS (Blue and Orange Lines)

   BLUE LINES (LONG/BUY):
   - Horizontal lines on the chart
   - Numbers show signal strength (0-7)
   - Bot buys when price reaches these levels
   - Lower lines = better buy prices

   ORANGE LINES (SHORT/SELL):
   - Horizontal lines on the chart
   - Numbers show signal strength (0-7)
   - Bot sells when price reaches these levels
   - Higher lines = better sell prices

8.2 ACCOUNT VALUE CHART

   CYAN LINE (Total Account Value):
   - Your total account worth
   - Includes EUR balance + cryptocurrency holdings
   - Shows overall account performance

   ORANGE LINE (Holdings Value):
   - Current value of your cryptocurrency holdings
   - What you would get if you sold everything
   - Shows trading performance

   TRADE MARKERS:
   - Red dots: BUY orders
   - Green dots: SELL orders
   - Purple dots: DCA (Dollar-Cost Averaging) orders

8.3 COIN CHARTS

   PRICE CHART:
   - Shows historical price movement
   - Candlestick or line chart
   - Timeframe selectable (1min to 1week)

   CURRENT PRICE:
   - Horizontal line showing current market price
   - Updates in real-time

================================================================================
                             9. TROUBLESHOOTING
================================================================================

9.1 "NOT TRAINED" STATUS

   PROBLEM: Coin shows "NOT TRAINED" in GUI
   SOLUTION:
   - Run the Trainer for that coin
   - Wait for training to complete
   - Status will update to "TRAINED"

9.2 NO NEURAL LINES ON CHART

   PROBLEM: Chart shows no blue/orange lines
   SOLUTION:
   - Ensure Neural Runner is running
   - Check that coin is trained
   - Wait a few minutes for signals to generate
   - Check runner_ready.json exists

9.3 TRADER NOT EXECUTING TRADES

   PROBLEM: No trades happening despite signals
   SOLUTION:
   - Check Neural Runner is running
   - Verify Trader is running
   - Check account has sufficient balance
   - Ensure trade amount is set correctly
   - Check signals are being generated (long_dca_signal.txt)

9.4 "LOT_SIZE" OR "NOTIONAL" ERRORS

   PROBLEM: Trade fails with filter error
   SOLUTION:
   - Bot automatically handles this
   - If manual trade fails, try larger amount
   - Minimum order value is usually 5-10 EUR

9.5 CHART SHOWS "NO DATA"

   PROBLEM: Account Value chart empty
   SOLUTION:
   - Ensure Trader is running
   - Wait for trader_status.json to be created
   - Chart will show current value from status file
   - Historical data accumulates over time

9.6 TELEGRAM BOT NOT RESPONDING

   PROBLEM: Bot doesn't answer commands
   SOLUTION:
   - Check telegram_token.txt exists and is correct
   - Check telegram_chat_id.txt exists and is correct
   - Restart telegram_bot.py
   - Verify bot is running (check process)

9.7 PROCESS EXITS IMMEDIATELY

   PROBLEM: Component starts then exits
   SOLUTION:
   - Check error messages in GUI log
   - Verify API keys are correct
   - Check internet connection
   - Verify Binance API permissions

================================================================================
                            10. IMPORTANT NOTES
================================================================================

10.1 SECURITY
   - NEVER share your API keys
   - Do NOT enable withdrawal permissions on Binance API
   - Keep binance_key.txt and binance_secret.txt secure
   - Use strong passwords

10.2 RISK MANAGEMENT
   - Start with small amounts
   - Monitor trades regularly
   - Set appropriate stop-loss levels
   - Don't invest more than you can afford to lose
   - Cryptocurrency trading is risky

10.3 BEST PRACTICES
   - Train all coins before starting trading
   - Let Neural Runner run for a few minutes before starting Trader
   - Monitor the GUI regularly
   - Check Telegram notifications
   - Review trade history periodically

10.4 FILE LOCATIONS

   Configuration:
   - gui_settings.json: Main settings
   - binance_key.txt: Binance API key
   - binance_secret.txt: Binance API secret
   - telegram_token.txt: Telegram bot token
   - telegram_chat_id.txt: Your Telegram chat ID

   Data Files:
   - hub_data/trader_status.json: Current trader status
   - hub_data/trade_history.jsonl: Trade history
   - hub_data/account_value_history.jsonl: Account value history
   - hub_data/runner_ready.json: Neural Runner readiness

   Coin Folders:
   - Each coin has its own folder (e.g., BTC/, ETH/)
   - Contains: long_dca_signal.txt, short_dca_signal.txt
   - Contains: low_bound_prices.html, high_bound_prices.html

10.5 STARTUP SEQUENCE

   RECOMMENDED ORDER:
   1. Start GUI (pt_hub_advanced.py)
   2. Click "Start All" (starts Neural Runner first)
   3. Wait for Neural Runner to be ready
   4. Trader starts automatically when ready
   5. Monitor via GUI or Telegram

   ALTERNATIVE:
   1. Start Neural Runner manually
   2. Wait for signals to generate
   3. Start Trader manually
   4. Monitor via GUI

10.6 SUPPORT

   For issues or questions:
   - Check this README first
   - Review error messages in GUI log
   - Check trader_status.json for current status
   - Verify all components are running
   - Check Binance API status

================================================================================
                              QUICK START GUIDE
================================================================================

1. Install dependencies: pip install -r requirements.txt
2. Add Binance API keys to binance_key.txt and binance_secret.txt
3. Edit gui_settings.json and add coins to trade
4. Run: python pt_hub_advanced.py
5. Click "Start All" in GUI
6. Wait for Neural Runner to be ready
7. Trader will start automatically
8. Monitor via GUI or Telegram

================================================================================

Good luck with your trading! Remember to start small and monitor regularly.

================================================================================



