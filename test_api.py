import os
import time
import hmac
import hashlib
import requests

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

def get_server_time():
    """Get Binance server time"""
    url = "https://api.binance.com/api/v3/time"
    response = requests.get(url)
    return response.json()['serverTime']

def get_account_balance(api_key, api_secret):
    """Get account balance using manual signed request"""
    # Get server time
    server_time = get_server_time()
    
    # Prepare query string
    query_string = f"timestamp={server_time}&recvWindow=60000"
    
    # Create signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Full query with signature
    full_query = f"{query_string}&signature={signature}"
    
    # Make request
    url = f"https://api.binance.com/api/v3/account?{full_query}"
    headers = {
        "X-MBX-APIKEY": api_key
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

if __name__ == "__main__":
    api_key, api_secret = get_api_credentials()
    
    if not api_key or not api_secret:
        print("Error: API keys not found. Please create binance_key.txt and binance_secret.txt")
        exit(1)
    
    print("Testing Binance API connection...")
    
    try:
        account = get_account_balance(api_key, api_secret)
        
        # Find EUR balance
        eur_balance = 0
        for asset in account['balances']:
            if asset['asset'] == 'EUR':
                eur_balance = float(asset['free'])
                print(f"EUR Balance: {eur_balance} EUR")
                break
        
        if eur_balance == 0:
            print("EUR balance not found or is 0")
        
        print("API connection successful!")
        
    except Exception as e:
        print(f"Error: {e}")
