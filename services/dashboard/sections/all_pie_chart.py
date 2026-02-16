import plotly.express as px
import streamlit as st


def display_pie_chart_all_coins() -> None:
    """Draw a pie chart of all coins in the portfolio."""
    st.subheader(
        "Distribution of all your holdings",
        help="Hover over each slice to see more details on current worth and share of total portfolio.",
    )

    df = st.session_state.portfolio_df

    # Always-dark mode
    text_color = "#FFFFFF"
    color_sequence = px.colors.sequential.Bluyl_r

    fig = px.pie(
        df,
        values="Current_Worth",
        names="Coin",
        hole=0.0,
        color_discrete_sequence=color_sequence,
    )

    fig.update_traces(
        textinfo="percent+label",
        textfont=dict(color=text_color, size=14),
        insidetextfont=dict(color=text_color, size=14),
        outsidetextfont=dict(color=text_color, size=14),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Current Worth: %{value:,.2f}€<br>"
            "Portfolio Share: %{percent}<extra></extra>"
        ),
        sort=False,
    )

    # Keep chart background adaptive + make hover readable in both modes
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  # transparent (adapts to Streamlit theme)
        plot_bgcolor="rgba(0,0,0,0)",  # transparent (adapts to Streamlit theme)
        font=dict(color=text_color),
        legend=dict(
            title="Coins",
            font=dict(color=text_color),
        ),
        hoverlabel=dict(
            bgcolor="#111827",
            font_color="#FFFFFF",
            bordercolor="#374151",
        ),
        margin=dict(t=20, b=20, l=20, r=20),
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
