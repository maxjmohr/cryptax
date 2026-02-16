import streamlit as st


def filter_coins() -> None:
    """Filter coins to display statistics of"""
    st.session_state.filtered_coins = st.multiselect(
        "Filter your holdings",
        options=st.session_state.portfolio_df["Coin"].to_list(),
        default=st.session_state.portfolio_df["Coin"].to_list(),
        help="Select which coins to include in the charts and statistics. By default, all coins are included",
        width="stretch",
        # label_visibility="collapsed",
    )
