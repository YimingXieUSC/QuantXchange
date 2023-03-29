import http.client
import pandas as pd
import json
import hmac
import hashlib
import time
import base64

API_KEY = 'IPPYi4Pu3iycdv5i'
API_SECRET = '7r84DJuwxJUOF906tBrr2Ydzbaaes3fA'
BASE_URL = 'api.coinbase.com'

ACCOUNTS = {'USD': '22595e72-6fc4-5d7d-be9d-2f464b326d71',
            "BTC": '71a5175a-2ebf-55f7-8d82-1c912a0d2ee3',
            'ETH': 'd8e39c57-f57b-501f-b82b-b26483b4d9c1'}


def send_request(endpoint, method='GET', body=''):
    timestamp = str(int(time.time()))
    message = timestamp + method + endpoint.split('?')[0] + str(body)
    signature = hmac.new(API_SECRET.encode(
        'utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()

    conn = http.client.HTTPSConnection(BASE_URL)
    payload = body
    headers = {
        'Content-Type': 'application/json',
        'CB-ACCESS-KEY': API_KEY,
        'CB-ACCESS-SIGN': signature.hex(),
        'CB-ACCESS-TIMESTAMP': timestamp,
    }
    conn.request(method, endpoint, payload, headers)
    res = conn.getresponse()
    data = res.read()
    # print(data.decode('utf-8'))
    return json.loads(data.decode('utf-8'))


def get_available_balance(currency):
    data = send_request(
        '/api/v3/brokerage/accounts/{}'.format(ACCOUNTS[currency]))
    return data['account']['available_balance']['value']


def get_historical_data(trading_pair, start, end, granularity):
    data = send_request('/api/v3/brokerage/products/{}/candles?start={}&end={}&granularity={}'.format(
        trading_pair, start, end, granularity))
    df = pd.DataFrame(
        data['candles'], columns=['start', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['start'], unit='s')
    return df


def moving_average_crossover(data, short_window, long_window):
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()

    buy_signals = (data['short_ma'].shift(1) < data['long_ma'].shift(1)) & (
        data['short_ma'] > data['long_ma'])
    sell_signals = (data['short_ma'].shift(1) > data['long_ma'].shift(1)) & (
        data['short_ma'] < data['long_ma'])

    return buy_signals, sell_signals


if __name__ == '__main__':
    trading_pair = 'BTC-USD'
    short_window = 20
    long_window = 50

    while True:
        timestamp = int(time.time())
        # Get historical data
        historical_data = get_historical_data(
            trading_pair, timestamp-long_window*60*60, timestamp, 'ONE_HOUR')  # 1-hour candles

        # Calculate moving averages
        buy_signals, sell_signals = moving_average_crossover(
            historical_data, short_window, long_window)

        if buy_signals.iloc[-1]:
            # Buy
            available_usd = get_available_balance('USD')
            price = historical_data['close'].iloc[-1]
            size = available_usd / price
            payload = json.dumps({
                'client_order_id': '0000-00000-000000',
                'product_id': trading_pair,
                'side': 'BUY',
                "order_configuration": {
                    "market_market_ioc": {
                        "quote_size": size,
                    }
                }
            })
            order = send_request('/api/v3/brokerage/orders', 'POST', payload)
            print('Buy order placed:')
            print(order)
            print()

        if sell_signals.iloc[-1]:
            # Sell
            available_btc = get_available_balance('BTC')
            payload = json.dumps({
                'client_order_id': '0000-00000-000000',
                'product_id': trading_pair,
                'side': 'SELL',
                "order_configuration": {
                    "market_market_ioc": {
                        "base_size": available_btc
                    }
                }
            })
            order = send_request('/api/v3/brokerage/orders', 'POST', payload)
            print('Sell order placed:')
            print(order)
            print()

        time.sleep(3600)  # Wait for 1 hour before checking again
