from __future__ import annotations

from datetime import date
from typing import List

import numpy as np
import pandas as pd
import streamlit as st

from upbit_quant.visualization.pulse_network_3d import (
    PulseNetworkConfig,
    build_pulse_network_figure,
)


st.set_page_config(
    page_title="UPbit-Quant Dashboard",
    page_icon="📈",
    layout="wide",
)


def _render_home() -> None:
    st.title("UPbit-Quant — Dashboard")
    st.write(
        """
This project started as an experimental quant-trading platform (RL/backtesting + data collection),
but much of the UI is prototype-grade.

Use the sidebar to switch features. The most “alive” view is **Pulse Network (3D)**:
- nodes are coins
- edges are rolling correlations (green=positive, red=negative)
- node size/color “pulses” with volatility and last return
"""
    )


def _render_fear_greed_demo() -> None:
    st.header("Fear/Greed (demo)")
    st.caption("This page uses synthetic data (random) — kept for historical context.")

    date_range = pd.date_range(start="2019-01-01", end="2021-12-31", freq="B")
    fear_index = np.random.randint(low=0, high=100, size=len(date_range))
    greed_index = np.random.randint(low=0, high=100, size=len(date_range))

    df = pd.DataFrame(
        {"Date": date_range, "Fear Index": fear_index, "Greed Index": greed_index}
    )

    st.sidebar.subheader("Fear/Greed thresholds")
    fear_threshold = st.sidebar.slider("Fear Threshold", 0.0, 1.0, 0.7, key="fear_thr")
    greed_threshold = st.sidebar.slider(
        "Greed Threshold", 0.0, 1.0, 0.7, key="greed_thr"
    )

    trade_potential = np.where(
        (greed_index / (greed_index + fear_index)) > greed_threshold,
        -1,
        np.where(
            (fear_index / (greed_index + fear_index)) > fear_threshold,
            1,
            0,
        ),
    )
    df["Trade Potential"] = trade_potential

    st.dataframe(df, use_container_width=True, height=260)

    import plotly.express as px

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Fear Index")
        st.plotly_chart(
            px.area(df, x="Date", y="Fear Index", title="Fear Index Over Time"),
            use_container_width=True,
        )
    with c2:
        st.subheader("Greed Index")
        st.plotly_chart(
            px.area(df, x="Date", y="Greed Index", title="Greed Index Over Time"),
            use_container_width=True,
        )

    st.subheader("Trade Potential")
    st.plotly_chart(
        px.line(df, x="Date", y="Trade Potential", title="Trade Potential Over Time"),
        use_container_width=True,
    )


def _render_pulse_network_3d() -> None:
    st.header("Pulse Network (3D)")
    st.caption(
        "Rolling correlation network from real price data (via yfinance). "
        "Tip: start with 5–12 symbols and a modest edge threshold."
    )

    st.sidebar.subheader("Pulse Network (3D) settings")
    symbols_text = st.sidebar.text_input(
        "Symbols (comma separated)",
        value="BTC,ETH,SOL,BNB,XRP,ADA,DOGE,DOT,AVAX,LINK",
        help="Examples: BTC,ETH or BTC-USD,ETH-USD",
    )
    symbols: List[str] = [s.strip() for s in symbols_text.split(",") if s.strip()]

    interval = st.sidebar.selectbox(
        "Interval", ["15m", "30m", "1h", "4h", "1d"], index=2
    )
    window = st.sidebar.slider("Rolling window (bars)", min_value=24, max_value=300, value=72)
    corr_threshold = st.sidebar.slider(
        "Edge threshold |corr|",
        min_value=0.10,
        max_value=0.95,
        value=0.55,
        step=0.05,
    )
    max_edges = st.sidebar.slider("Max edges", min_value=10, max_value=300, value=120, step=10)

    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        start = st.date_input("Start", value=date(2024, 1, 1))
    with colB:
        end = st.date_input("End", value=date.today())
    with colC:
        st.write("")
        st.write("")
        run = st.button("Build / Refresh", type="primary", use_container_width=True)

    if run or "pulse_last" not in st.session_state:
        st.session_state["pulse_last"] = {
            "symbols": symbols,
            "start": start,
            "end": end,
            "interval": interval,
            "window": window,
            "corr_threshold": corr_threshold,
            "max_edges": max_edges,
        }

    last = st.session_state["pulse_last"]
    cfg = PulseNetworkConfig(
        symbols=last["symbols"],
        start=last["start"],
        end=last["end"],
        interval=last["interval"],
        window=int(last["window"]),
        corr_threshold=float(last["corr_threshold"]),
        max_edges=int(last["max_edges"]),
    )

    with st.spinner("Fetching prices + building 3D network..."):
        fig, meta = build_pulse_network_figure(cfg)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Debug / data preview", expanded=False):
        prices = meta.get("prices")
        corr = meta.get("corr")
        edges = meta.get("edges")
        if isinstance(prices, pd.DataFrame):
            st.write("**Prices (tail)**")
            st.dataframe(prices.tail(10), use_container_width=True)
        if isinstance(corr, pd.DataFrame):
            st.write("**Correlation (tail window)**")
            st.dataframe(corr.round(3), use_container_width=True)
        if isinstance(edges, list):
            st.write("**Edges (top)**")
            st.write(edges[:30])


def main() -> None:
    st.sidebar.title("UPbit-Quant")
    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Pulse Network (3D)", "Fear/Greed (demo)"],
        index=1,
    )

    if page == "Home":
        _render_home()
    elif page == "Pulse Network (3D)":
        _render_pulse_network_3d()
    else:
        _render_fear_greed_demo()


if __name__ == "__main__":
    main()
