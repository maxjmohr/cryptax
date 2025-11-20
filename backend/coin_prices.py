import time

import requests
from requests.models import Response


def fetch_live_coin_prices(coin: str, currency: str) -> float:
    """Fetch live coin prices from CoinGecko API.
    Args:
        coin (str): The coin symbol to fetch prices for.
        currency (str): The currency to fetch the price in (usd, eur, gbp).
    Returns:
        price (float): The current price of the coin in the specified currency.
    """
    coin = coin.lower()
    currency = currency.lower()

    url: str = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies={currency}"
    response: Response = requests.get(url=url)

    time.sleep(1)  # To respect API rate limits

    if response.status_code != 200:
        raise ConnectionError(f"Failed to fetch prices for {coin} from CoinGecko.")

    data = response.json()

    if coin not in data:
        raise ValueError(f"Coin {coin} not found in CoinGecko response.")

    price: float = data[coin][currency]
    return price


if __name__ == "__main__":
    coin: str = "Bitcoin"
    currency: str = "EUR"
    price: float = fetch_live_coin_prices(coin, currency)
    print(f"The current price of {coin} is {price} {currency}.")
