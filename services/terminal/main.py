import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "./../../")))

from typing import Tuple

import polars as pl
from dotenv import load_dotenv
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static

from backend.portfolio import Portfolio

# Load the environment variables (locally)
dotenv_path: str = os.path.join(os.path.dirname(__file__), "./../../.env")
try:
    load_dotenv(dotenv_path)
except Exception:
    print(f"No .env file found at {dotenv_path}, skipping...")
    pass

# Read env variable
HIDE_CRITICAL_VALUES: bool = (
    os.environ.get("HIDE_CRITICAL_VALUES", "").lower() == "true"
)


def display_returns_nicely(value: float) -> Text:
    """Display the returns nicely with arrows and colors"""
    pct_val = value * 100
    if pct_val > 0:
        return Text(f"↑ {pct_val:.2f}%", style="green")
    elif pct_val < 0:
        return Text(f"↓ {pct_val:.2f}%", style="red")
    else:
        return Text(f"→ {pct_val:.2f}%")


def display_monetary_values_nicely(value: float | str):
    """Display monetary values nicely such as 1,000,000.00"""
    if HIDE_CRITICAL_VALUES:
        return value
    return f"{value:,.2f}"


def hide_critical_values(data: pl.DataFrame) -> pl.DataFrame:
    """Hide critical data such as user id or monetary values if HIDE_CRITICAL_VALUES=true"""
    if not HIDE_CRITICAL_VALUES:
        return data

    # Set critical columns
    critical_columns: list[str] = [
        "User_ID",
        "Total_Holdings",
        "Total_Fiat_Invested",
        "Current_Worth",
        "Invested_Since",
    ]

    # Replace all values
    for col in critical_columns:
        if col in data.columns:
            data = data.with_columns(pl.lit("******").alias(col))

    return data


def prepare_data() -> Tuple[
    int | str, datetime, str, float | str, float | str, float | str, float, pl.DataFrame
]:
    """Prepare data to display in terminal"""
    # Get current portfolio and prices
    portfolio: Portfolio = Portfolio()

    # Calculate current worth
    portfolio.calculate_current_worth()

    # Calculate returns
    portfolio.calculate_returns()

    # Create output_df
    output_df: pl.DataFrame = portfolio.df

    # Hide critical values if configured
    output_df = hide_critical_values(output_df)

    # Extract necessary objects to output
    user_id: int | str = output_df["User_ID"][0]
    price_timestamp: datetime = portfolio.df["Price_Timestamp"][0]

    # Get deposit and filter out
    deposit_row: pl.DataFrame = output_df.filter(pl.col("Coin") == "EUR")
    deposit_currency: str = deposit_row["Coin"][0]
    deposit_total_fiat_invested: float = deposit_row["Total_Fiat_Invested"][0]
    output_df = output_df.filter(pl.col("Coin") != "EUR")

    # Get total return
    sums: pl.DataFrame = (
        portfolio.df.select(  # portfolio.df because we need actual values for return
            [
                pl.sum("Total_Fiat_Invested").alias("entire_total_fiat_invested"),
                pl.sum("Current_Worth").alias("entire_current_worth"),
            ]
        )
    )
    entire_total_fiat_invested: float | str = sums["entire_total_fiat_invested"][0]
    entire_current_worth: float | str = sums["entire_current_worth"][0]
    entire_current_return: float = float(entire_current_worth) / float(
        entire_total_fiat_invested
    )
    # Also hide if configured
    if HIDE_CRITICAL_VALUES:
        entire_total_fiat_invested = "******"
        entire_current_worth = "******"

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
    user_id: int | str,
    price_timestamp: datetime,
    deposit_currency: str,
    deposit_total_fiat_invested: float | str,
    entire_total_fiat_invested: float | str,
    entire_current_worth: float | str,
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
