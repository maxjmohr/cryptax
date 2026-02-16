import streamlit as st
from load_data import load_portfolio
from sections.all_pie_chart import display_pie_chart_all_coins
from sections.filters import filter_coins


def main() -> None:
    # Page config
    st.set_page_config(
        page_title="cryptax",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Titles
    st.title("Explore your crypto portfolio!")

    # Load relevant data
    load_portfolio()

    # Filter coins with multiselect
    col1, col2 = st.columns([1, 1])
    with col1:
        filter_coins()

    # Sections
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        # Pie chart of all coins
        display_pie_chart_all_coins()

    # Footer
    st.divider()
    st.caption(
        "Powered by cryptax",
        text_alignment="center",
    )
    st.caption(
        "This dashboard is for informational purposes only and should not be considered financial advice. Always do your own research before making any investment decisions.",
        text_alignment="center",
    )


if __name__ == "__main__":
    main()
