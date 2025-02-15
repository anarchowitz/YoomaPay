import requests

def get_crypto_rates():
    api_key = "a47a4eaf-1eab-4867-805f-6d9fd5a45b20"
    api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {
        "symbol": ",".join(['USDT', 'TON', 'BTC', 'DOGE', 'LTC', 'ETH', 'BNB', 'TRX', 'USDC']),
        "convert": "RUB"
    }
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key
    }
    response = requests.get(api_url, params=params, headers=headers)
    data = response.json()
    rates = {}
    if 'data' in data:
        for symbol in data["data"]:
            rates[symbol] = data["data"][symbol]["quote"]["RUB"]["price"]
    else:
        print("Ошибка: ключ 'data' не найден в ответе API")
    return rates

rates = get_crypto_rates()
print(rates)