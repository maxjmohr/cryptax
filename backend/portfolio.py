import json
import os
from datetime import datetime

import polars as pl
from coin_prices import fetch_live_coin_prices
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

        # Calculate current worth
        self.calculate_current_worth()

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

    def calculate_current_worth(self) -> None:
        """Calculate the current worth of the holdings"""
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
                "Coin_Price",
                "Current_Worth",
                "Current_Return",
                "Price_Timestamp",
            ]
        ).sort("Current_Worth", descending=True)

    def output_excel(self, file_path: str) -> None:
        """Output the DataFrame to an Excel file.
        Args:
            file_path (str): The path to the output Excel file.
        """
        self.df.write_excel(file_path)


if __name__ == "__main__":
    portfolio = Portfolio()
    print(portfolio.df)
    # Export as xlsx
    portfolio.output_excel("output_portfolio.xlsx")
