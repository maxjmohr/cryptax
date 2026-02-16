import streamlit as st
from load_data import load_portfolio
from sections.all_pie_chart import display_pie_chart_all_coins


def main() -> None:
    # Page config
    st.set_page_config(
        page_title="cryptax",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Titles
    st.title("Explore your crypto portfolio!")
    st.write("Powered by cryptax")

    # Load relevant data
    load_portfolio()

    # Sections
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        # Pie chart of all coins
        display_pie_chart_all_coins()


if __name__ == "__main__":
    main()
