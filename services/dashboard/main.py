import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="cryptax",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("Explore your crypto portfolio!")
    st.write("Powered by cryptax")


if __name__ == "__main__":
    main()
