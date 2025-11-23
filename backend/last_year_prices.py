import json
import os
from datetime import datetime, timedelta
from functools import reduce

import polars as pl
from progress.spinner import PixelSpinner

from .fetch_coin_prices import fetch_historical_prices_range


class LastYearPrices:
    # Class elements we expect
    __slots__: tuple = (
        "df",
        "relevant_coins",
    )

    def __init__(self) -> None:
        # Read relevant coins
        self.read_coins()

        # Fetch data
        self.fetch_daily_last_year_prices()

    def read_coins(self) -> None:
        # Read the relevant coins from their json mapping
        json_path: str = os.path.join(os.path.dirname(__file__), "coin_mapping.json")
        with open(json_path, "r") as f:
            coin_mapping: dict = json.load(f)

        # Turn into list
        self.relevant_coins: list[str] = list(coin_mapping.values())

    @staticmethod
    def fetch_one_coin(
        coin_name: str,
        currency: str,
        start_date: datetime,
        end_date: datetime,
        bar,
    ) -> pl.DataFrame:
        """Fetch last year prices for one coin and store as pl.DataFrame"""
        # Fetch prices
        data: pl.DataFrame = fetch_historical_prices_range(
            coin_name, currency, start_date=start_date, end_date=end_date
        )

        # Rename price into coin_name
        data: pl.DataFrame = data.rename({"Price": coin_name})

        # Update progress bar
        bar.next()

        return data

    @staticmethod
    def reorder_columns(data: pl.DataFrame) -> pl.DataFrame:
        """Reorder the coins alphabetically"""
        # Reorder columns: first Price_Timestamp, then alphabetical
        cols: list[str] = data.columns
        ordered_cols: list[str] = ["Price_Timestamp"] + sorted(
            [c for c in cols if c != "Price_Timestamp"]
        )
        return data.select(ordered_cols)

    @staticmethod
    def extract_timestamp_day(data: pl.DataFrame) -> pl.DataFrame:
        """Turn the timestamp into date only (not hms)"""
        return data.with_columns(
            pl.col("Price_Timestamp").dt.date().alias("Price_Timestamp")
        )

    def fetch_daily_last_year_prices(self) -> None:
        """Fetch last year prices"""
        # Prepare dates
        today: datetime = datetime.today()
        last_year: datetime = today - timedelta(days=365)

        # Make sure bitcoin is the first coin loaded to ensure the coin exists at least a year
        sorted_coins: list[str] = sorted(
            self.relevant_coins, key=lambda x: 0 if x.lower() == "bitcoin" else 1
        )

        # Load prices for each coin as dataframes
        with PixelSpinner(
            f"Fetching historical coin prices ({last_year.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')})… "
        ) as bar:
            dfs: list[pl.DataFrame] = [
                self.fetch_one_coin(
                    coin_name=coin,
                    currency="EUR",
                    start_date=last_year,
                    end_date=today,
                    bar=bar,
                )
                for coin in sorted_coins
            ]

        # Left join of dataframes into one
        data: pl.DataFrame = reduce(
            lambda left, right: left.join(right, on="Price_Timestamp", how="left"), dfs
        )

        # Sort by timestamp (ascending)
        data = data.sort("Price_Timestamp", descending=False)

        # Reorder columns
        data = self.reorder_columns(data)

        # Turn timestamp into day
        self.df = self.extract_timestamp_day(data)

    def update_todays_prices(self, data: pl.DataFrame) -> None:
        """Update todays prices with live prices"""
        # Make sure order is correct
        data = self.reorder_columns(data)

        # Turn timestamp into day
        data = self.extract_timestamp_day(data)

        # Check, if timestamp exists
        ts: float = data.select("Price_Timestamp").to_numpy()[0]

        if ts in self.df["Price_Timestamp"].to_list():
            # Delete existing today's price
            self.df = self.df.filter(pl.col("Price_Timestamp") != ts)

        # Append new row (live price)
        self.df = pl.concat([self.df, data])


if __name__ == "__main__":
    last_year_prices = LastYearPrices()
    print(last_year_prices.df)
