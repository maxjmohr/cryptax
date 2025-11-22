import json
import os
from datetime import datetime, timedelta

import polars as pl
from fetch_coin_prices import fetch_live_coin_prices
from last_year_prices import LastYearPrices
from transactions import Transactions


class Portfolio:
    # Class elements we expect
    __slots__: tuple = ("df",)

    def __init__(self) -> None:
        # Get transactions data as base df
        self.df = Transactions().df

        # Calculate deposit
        self.calculate_deposit()

        # Group by coin
        self.group_by_coin()

        # Drop coins with 0 holdings except deposit
        self.drop_zero_holdings()

        # Map coin symbols to names
        self.map_coin_symbols_to_names()

    def calculate_deposit(self) -> None:
        """Calculate the current deposit of fiat currency in the portfolio."""
        # Calculate total deposit
        deposit: float = sum(self.df["Change_Fiscal"].drop_nulls())

        # Add deposit as new row
        deposit_row = pl.DataFrame(
            {
                "User_ID": [self.df["User_ID"][0]],
                "UTC_Time": [datetime.now()],
                "Account": ["Spot"],
                "Operation": ["Deposit_Calculated"],
                "Coin": ["EUR"],
                "Change_Coin": [None],
                "Currency": [None],
                "Change_Fiscal": [deposit],
                "Price_per_Coin": [None],
                "source_file": [None],
            }
        )

        # Delete rows where Operation = Deposit or Fiat Deposit
        self.df = self.df.filter(
            ~(self.df["Operation"].is_in(["Deposit", "Fiat Deposit"]))
        )

        self.df = pl.concat([self.df, deposit_row])

    def group_by_coin(self) -> None:
        """Group the portfolio by coin and calculate total holdings."""
        grouped_df = self.df.group_by("User_ID", "Coin").agg(
            [
                pl.sum("Change_Coin").alias("Total_Holdings"),
                pl.sum("Change_Fiscal").abs().alias("Total_Fiat_Invested"),
                pl.min("UTC_Time").alias("Invested_Since"),
            ]
        )
        self.df = grouped_df

    def drop_zero_holdings(self) -> None:
        """Drop coins with 0 holdings except for EUR (deposit)"""
        self.df = self.df.filter(
            (self.df["Total_Holdings"] != 0.0) | (self.df["Coin"] == "EUR")
        )

    def map_coin_symbols_to_names(self) -> None:
        """Map the short symbols of the coins to their names (except EUR)"""
        # Read the json with the mappings
        json_path: str = os.path.join(os.path.dirname(__file__), "coin_mapping.json")
        with open(json_path, "r") as f:
            coin_mapping: dict = json.load(f)

        # Map names into new column "Coin_Name"
        self.df = self.df.with_columns(
            pl.col("Coin")
            .map_elements(lambda x: coin_mapping.get(x, None))
            .alias("Coin_Name")
        )

    def calculate_current_worth(self) -> pl.DataFrame:
        """Calculate the current worth of the holdings
        Also output a df row with the prices to attach to LastYearPrices object
        """
        # Fetch current coin prices
        self.df = self.df.with_columns(
            pl.when(pl.col("Coin") == "EUR")
            .then(pl.col("Total_Fiat_Invested"))
            .otherwise(
                pl.col("Coin_Name").map_elements(
                    lambda c: fetch_live_coin_prices(c, "EUR"),
                    return_dtype=pl.Float64,
                )
            )
            .alias("Coin_Price")
        )

        # Calculate current worth
        self.df = self.df.with_columns(
            (pl.col("Coin_Price") * pl.col("Total_Holdings")).alias("Current_Worth")
        )

        # Calculate return
        self.df = self.df.with_columns(
            (
                (pl.col("Current_Worth") - pl.col("Total_Fiat_Invested"))
                / pl.when(pl.col("Total_Fiat_Invested") == 0)
                .then(0.001)
                .otherwise(pl.col("Total_Fiat_Invested"))
            ).alias("Current_Return")
        )
        # Add coin price date
        self.df = self.df.with_columns(pl.lit(datetime.now()).alias("Price_Timestamp"))

        # Reorder and sort df
        self.df = self.df.select(
            [
                "User_ID",
                "Coin",
                "Coin_Name",
                "Total_Holdings",
                "Total_Fiat_Invested",
                "Invested_Since",
                "Coin_Price",
                "Current_Worth",
                "Current_Return",
                "Price_Timestamp",
            ]
        ).sort("Current_Worth", descending=True)

        # Create df row output for LastYearPrices object
        last_year_prices_row: pl.DataFrame = (
            self.df.filter(pl.col("Coin") != "EUR")  # <-- hier filtern
            .select(["Price_Timestamp", "Coin_Name", "Coin_Price"])
            .pivot(on="Coin_Name", index="Price_Timestamp", values="Coin_Price")
        )

        return last_year_prices_row

    def output_excel(self, file_path: str) -> None:
        """Output the DataFrame to an Excel file.
        Args:
            file_path (str): The path to the output Excel file.
        """
        self.df.write_excel(file_path)

    def calculate_returns(self) -> None:
        """Calculate returns for different periods: 1y, 6m, 3m, 1m, 1w"""
        # Get target dates
        today = datetime.today().date()
        raw_periods: dict = {
            "1w": today - timedelta(days=7),
            "1m": today - timedelta(days=30),
            "3m": today - timedelta(days=91),
            "6m": today - timedelta(days=182),
            "YtD": today.replace(month=1, day=1),
            "1y": today
            - timedelta(
                days=364
            ),  # 364 because maximum history for demo CoinGecko account
        }

        # Sort dates in dict based on difference to today
        periods: dict = dict(
            sorted(raw_periods.items(), key=lambda x: (today - x[1]).days)
        )

        # Prepare dataframes
        df: pl.DataFrame = self.df
        last_prices: pl.DataFrame = LastYearPrices().df

        # Melt LastYearPrices: Coins as variables, Price as values
        last_prices_long: pl.DataFrame = last_prices.unpivot(
            index=["Price_Timestamp"],
            on=[c for c in last_prices.columns if c != "Price_Timestamp"],
            variable_name="Coin_Name",
            value_name="Past_Price",
        )

        # Calculate returns for each period
        for period_name, past_date in periods.items():
            # Get Past_Price for each coin at this date
            last_prices_long_period: pl.DataFrame = last_prices_long.filter(
                pl.col("Price_Timestamp") == past_date
            ).drop("Price_Timestamp")

            # Join price
            df_period: pl.DataFrame = df.join(
                last_prices_long_period, on="Coin_Name", how="left"
            )

            # Calculate and store return
            df: pl.DataFrame = df_period.with_columns(
                (
                    (pl.col("Coin_Price") - pl.col("Past_Price")) / pl.col("Past_Price")
                ).alias(f"{period_name}_Return")
            ).drop("Past_Price")

        self.df = df


if __name__ == "__main__":
    portfolio = Portfolio()
    last_year_prices_row = portfolio.calculate_current_worth()
    print(portfolio.df)
    print(last_year_prices_row)
    portfolio.calculate_returns()
    print(portfolio.df)
    # Export as xlsx
    portfolio.output_excel("output_portfolio.xlsx")
