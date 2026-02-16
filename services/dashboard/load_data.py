import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "./../../")))

import polars as pl
import streamlit as st

from backend.portfolio import Portfolio


def load_portfolio() -> None:
    """Load current portfolio with values into session"""
    # Get current portfolio and prices
    portfolio: Portfolio = Portfolio()

    # Calculate current worth
    portfolio.calculate_current_worth()

    # Calculate returns
    portfolio.calculate_returns()

    # Store in session
    st.session_state.portfolio = portfolio

    # Extract necessary objects to display
    st.session_state.user_id = portfolio.df["User_ID"][0]
    st.session_state.price_timestamp = portfolio.df["Price_Timestamp"][0]

    # Get deposit and filter out
    deposit_row: pl.DataFrame = portfolio.df.filter(pl.col("Coin") == "EUR")
    st.session_state.deposit_currency = deposit_row["Coin"][0]
    st.session_state.deposit_total_fiat_invested = deposit_row["Total_Fiat_Invested"][0]
    portfolio.df = portfolio.df.filter(pl.col("Coin") != "EUR")

    # Create output dataframe
    portfolio.df = portfolio.df.select(
        pl.exclude(
            [
                "User_ID",
                "Price_Timestamp",
            ]
        )
    ).sort("Current_Worth", descending=True)

    # Store portfolio df
    st.session_state.portfolio_df = portfolio.df
