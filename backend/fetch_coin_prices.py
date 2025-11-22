import os
import time
from datetime import datetime, timedelta

import polars as pl
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

# Try to fetch COINGECKO_API_KEY
COINGECKO_API_KEY: str | None = os.environ.get("COINGECKO_API_KEY")


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

    data: dict = response.json()

    if coin not in data:
        raise ValueError(f"Coin {coin} not found in CoinGecko response.")

    print(f"Found current price for {coin}")
    price: float = data[coin][currency]
    return price


def fetch_historical_prices_range(
    coin: str,
    currency: str,
    start_date: datetime,
    end_date: datetime,
) -> pl.DataFrame:
    """
    Fetch historical prices for a coin from CoinGecko for a given date range.
    """
    coin = coin.lower()
    currency = currency.lower()

    # Convert to UNIX timestamps (seconds)
    start_ts: int = int(start_date.timestamp())
    end_ts: int = int(end_date.timestamp())

    url: str = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart/range"
    params: dict = {
        "vs_currency": currency,
        "from": start_ts,
        "to": end_ts,
    }

    # If there is an API key, insert it
    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY
        print(
            f"Fetching coin prices for {coin} with CoinGecko API key "
            f"from {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        print(
            f"No CoinGecko API key found, fetching coin prices for {coin} without key "
            f"from {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}"
        )

    response: Response = requests.get(url, params=params)

    # CoinGecko Demo rate limit: 30 requests/minute
    time.sleep(30 / 60)

    if response.status_code != 200:
        raise ConnectionError(
            f"Failed to fetch market chart range: {response.status_code}, {response.text}"
        )

    data: dict = response.json()

    prices = data.get("prices")
    if not prices:
        raise ValueError(f"No price data available for {coin} in the given range.")

    # Turn into dataframe
    df: pl.DataFrame = pl.DataFrame(
        {
            "Price_Timestamp": [p[0] for p in prices],
            "Price": [p[1] for p in prices],
        }
    )

    df: pl.DataFrame = df.with_columns(
        pl.col("Price_Timestamp").cast(pl.Datetime("ms"))
    ).select(["Price_Timestamp", "Price"])

    return df


if __name__ == "__main__":
    print("Fetching data...")
    coin: str = "Bitcoin"
    currency: str = "EUR"
    today: datetime = datetime.today()
    last_week: datetime = today - timedelta(days=7)

    price: float = fetch_live_coin_prices(coin, currency)
    historical_prices: pl.DataFrame = fetch_historical_prices_range(
        coin, currency, start_date=last_week, end_date=today
    )

    print(f"\n{coin}\nCurrent price: {price} {currency}")

    print("\nHistorical prices:")
    print(historical_prices)
