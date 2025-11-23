import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "./../../")))

from typing import Tuple

import polars as pl
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static

from backend.portfolio import Portfolio


def display_returns_nicely(value: float) -> Text:
    """Display the returns nicely with arrows and colors"""
    pct_val = value * 100
    if pct_val > 0:
        return Text(f"↑ {pct_val:.2f}%", style="green")
    elif pct_val < 0:
        return Text(f"↓ {pct_val:.2f}%", style="red")
    else:
        return Text(f"→ {pct_val:.2f}%")


def display_monetary_values_nicely(value: float):
    """Display monetary values nicely such as 1,000,000.00"""
    return f"{value:,.2f}"


def prepare_data() -> Tuple[
    int, datetime, str, float, float, float, float, pl.DataFrame
]:
    """Prepare data to display in terminal"""
    # Get current portfolio and prices
    portfolio: Portfolio = Portfolio()

    # Calculate current worth
    portfolio.calculate_current_worth()

    # Calculate returns
    portfolio.calculate_returns()

    # Extract necessary objects to output
    user_id: int = portfolio.df["User_ID"][0]
    price_timestamp: datetime = portfolio.df["Price_Timestamp"][0]

    # Get deposit and filter out
    deposit_row: pl.DataFrame = portfolio.df.filter(pl.col("Coin") == "EUR")
    deposit_currency: str = deposit_row["Coin"][0]
    deposit_total_fiat_invested: float = deposit_row["Total_Fiat_Invested"][0]
    output_df: pl.DataFrame = portfolio.df.filter(pl.col("Coin") != "EUR")

    # Get total return
    sums: pl.DataFrame = output_df.select(
        [
            pl.sum("Total_Fiat_Invested").alias("entire_total_fiat_invested"),
            pl.sum("Current_Worth").alias("entire_current_worth"),
        ]
    )
    entire_total_fiat_invested: float = sums["entire_total_fiat_invested"][0]
    entire_current_worth: float = sums["entire_current_worth"][0]
    entire_current_return: float = entire_current_worth / entire_total_fiat_invested

    # Create output dataframe
    output_df = output_df.select(
        pl.exclude(
            [
                "User_ID",
                "Price_Timestamp",
            ]
        )
    ).sort("Current_Worth", descending=True)

    return (
        user_id,
        price_timestamp,
        deposit_currency,
        deposit_total_fiat_invested,
        entire_total_fiat_invested,
        entire_current_worth,
        entire_current_return,
        output_df,
    )


def display_data(
    user_id: int,
    price_timestamp: datetime,
    deposit_currency: str,
    deposit_total_fiat_invested: float,
    entire_total_fiat_invested: float,
    entire_current_worth: float,
    entire_current_return: float,
    output_df: pl.DataFrame,
):
    """Nicely display data in terminal"""

    class TableApp(App):
        CSS_PATH = None
        # Columns to format as percentages with arrows
        pct_cols: list[str] = [
            "Current_Return",
            "1y_Return",
            "YtD_Return",
            "6m_Return",
            "3m_Return",
            "1m_Return",
            "1w_Return",
        ]

        # Columns to display nicely as monetary values
        mon_cols: list[str] = [
            "Total_Fiat_Invested",
            "Coin_Price",
            "Current_Worth",
        ]

        def compose(self) -> ComposeResult:
            # Basic information
            yield Static(f"User ID: {user_id} | Timestamp: {price_timestamp}")

            # Total return, worth and investments
            entire_current_return_nice: Text = display_returns_nicely(
                entire_current_return
            )
            yield Static(entire_current_return_nice)
            yield Static(
                f"Current Worth: {display_monetary_values_nicely(entire_current_worth)} {deposit_currency} | Total Invested: {display_monetary_values_nicely(entire_total_fiat_invested)} {deposit_currency}"
            )

            # Deposit
            yield Static(
                f"Deposit: {display_monetary_values_nicely(deposit_total_fiat_invested)} {deposit_currency}"
            )

            yield DataTable()

        def on_mount(self) -> None:
            table = self.query_one(DataTable)

            # Fix first two columns
            table.fixed_columns = 2

            # Add columns from DataFrame
            table.add_columns(*output_df.columns)

            # Add rows with formatting
            for i in range(output_df.height):
                row = []
                for col in output_df.columns:
                    val = output_df[col][i]
                    if col in self.pct_cols:
                        display_val: Text = display_returns_nicely(val)
                        row.append(display_val)
                    elif col in self.mon_cols:
                        nice_mon_value = display_monetary_values_nicely(val)
                        row.append(nice_mon_value)
                    else:
                        row.append(str(val))
                table.add_row(*row)

    app = TableApp()
    app.run()


def main() -> None:
    """Fetch current portfolio and display nicely in terminal"""
    # Fetch and prepare data
    (
        user_id,
        price_timestamp,
        deposit_currency,
        deposit_total_fiat_invested,
        entire_total_fiat_invested,
        entire_current_worth,
        entire_current_return,
        output_df,
    ) = prepare_data()

    # Display data
    display_data(
        user_id,
        price_timestamp,
        deposit_currency,
        deposit_total_fiat_invested,
        entire_total_fiat_invested,
        entire_current_worth,
        entire_current_return,
        output_df,
    )


if __name__ == "__main__":
    main()
