import os
import time

import requests
from dotenv import load_dotenv
from requests.models import Response

# Load the environment variables (locally)
dotenv_path: str = os.path.join(os.path.dirname(__file__), "./../.env")
try:
    load_dotenv(dotenv_path)
except Exception:
    print(f"No .env file found at {dotenv_path}, skipping...")
    pass


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

    url: str = "https://api.coingecko.com/api/v3/simple/price"
    params: dict = {"ids": coin, "vs_currencies": currency}

    # If there is an API key, insert it
    COINGECKO_API_KEY: str | None = os.environ.get("COINGECKO_API_KEY")

    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY
        print(f"Fetching coin price for {coin} with CoinGecko API key")
    else:
        print(f"No CoinGecko API key found, fetching coin price for {coin} without key")

    response: Response = requests.get(url, params=params)

    # CoinGecko Demo rate limit: 30 requests/minute
    time.sleep(30 / 60)

    if response.status_code != 200:
        raise ConnectionError(f"Failed to fetch prices for {coin} from CoinGecko.")

    data = response.json()

    if coin not in data:
        raise ValueError(f"Coin {coin} not found in CoinGecko response.")

    print(f"Found current price for {coin}")
    price: float = data[coin][currency]
    return price


if __name__ == "__main__":
    coin: str = "Bitcoin"
    currency: str = "EUR"
    price: float = fetch_live_coin_prices(coin, currency)
    print(f"The current price of {coin} is {price} {currency}.")
