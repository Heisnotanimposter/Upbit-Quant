from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PulseNetworkConfig:
    symbols: Sequence[str]
    start: Optional[date] = None
    end: Optional[date] = None
    interval: str = "1h"  # yfinance interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d...
    window: int = 72  # rolling window length in bars
    corr_threshold: float = 0.55  # absolute correlation threshold
    max_edges: int = 120  # cap for readability/performance
    seed: int = 7


def _as_yf_tickers(symbols: Sequence[str]) -> List[str]:
    # Heuristic: if user passes "BTC" treat as "BTC-USD"; if already has "-" keep.
    tickers: List[str] = []
    for s in symbols:
        s = s.strip().upper()
        if not s:
            continue
        if "-" in s:
            tickers.append(s)
        else:
            tickers.append(f"{s}-USD")
    return tickers


def fetch_prices_yfinance(
    symbols: Sequence[str],
    start: Optional[date],
    end: Optional[date],
    interval: str,
) -> pd.DataFrame:
    """
    Fetch close prices from yfinance.

    Returns a DataFrame indexed by timestamp with columns as symbols (the input symbols),
    containing float closes.
    """
    import yfinance as yf

    yf_tickers = _as_yf_tickers(symbols)
    raw = yf.download(
        tickers=" ".join(yf_tickers),
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
        interval=interval,
        group_by="column",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if raw is None or len(raw) == 0:
        return pd.DataFrame()

    # yfinance shape varies:
    # - multiple tickers -> columns MultiIndex: (field, ticker)
    # - single ticker -> columns: ['Open','High','Low','Close',...]
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"].copy()
        # Map yf tickers back to requested symbol labels
        mapping = {yf_sym: orig.strip().upper() for yf_sym, orig in zip(yf_tickers, symbols)}
        close = close.rename(columns=mapping)
        return close.sort_index()

    # single ticker
    sym = symbols[0].strip().upper()
    return raw[["Close"]].rename(columns={"Close": sym}).sort_index()


def _rolling_slice(df: pd.DataFrame, window: int, end_idx: int) -> pd.DataFrame:
    if df.empty:
        return df
    start_idx = max(0, end_idx - window + 1)
    return df.iloc[start_idx : end_idx + 1]


def _returns(prices: pd.DataFrame) -> pd.DataFrame:
    # log returns are more stable for correlation
    return np.log(prices).diff().replace([np.inf, -np.inf], np.nan).dropna(how="all")


def _top_edges_from_corr(
    corr: pd.DataFrame, threshold: float, max_edges: int
) -> List[Tuple[str, str, float]]:
    edges: List[Tuple[str, str, float]] = []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            w = float(corr.iloc[i, j])
            if np.isnan(w):
                continue
            if abs(w) >= threshold:
                edges.append((cols[i], cols[j], w))
    edges.sort(key=lambda t: abs(t[2]), reverse=True)
    return edges[:max_edges]


def build_pulse_network_figure(
    config: PulseNetworkConfig,
    *,
    frame_end_index: Optional[int] = None,
):
    """
    Build a 3D "living pulse" network figure.

    - Nodes: coins
    - Node size: rolling volatility (std of returns)
    - Node color: last return in the window (green up / red down)
    - Edges: correlation of returns within rolling window (green positive / red negative)
    """
    import networkx as nx
    import plotly.graph_objects as go

    prices = fetch_prices_yfinance(
        config.symbols, start=config.start, end=config.end, interval=config.interval
    )
    prices = prices.dropna(axis=1, how="all").ffill().dropna(axis=0, how="any")

    if prices.shape[1] < 2 or prices.shape[0] < max(5, config.window // 3):
        fig = go.Figure()
        fig.update_layout(
            title="Pulse Network (3D) — not enough data",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        return fig, {"prices": prices}

    rets = _returns(prices).dropna(axis=1, how="any")
    if rets.empty or rets.shape[1] < 2:
        fig = go.Figure()
        fig.update_layout(
            title="Pulse Network (3D) — not enough return data",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        return fig, {"prices": prices, "returns": rets}

    end_idx = frame_end_index if frame_end_index is not None else (len(rets) - 1)
    end_idx = int(np.clip(end_idx, 0, len(rets) - 1))
    win = _rolling_slice(rets, config.window, end_idx)

    corr = win.corr()
    edges = _top_edges_from_corr(corr, config.corr_threshold, config.max_edges)

    G = nx.Graph()
    for s in corr.columns:
        G.add_node(s)
    for a, b, w in edges:
        G.add_edge(a, b, weight=w)

    # 3D spring layout for stable spatial meaning across frames
    pos = nx.spring_layout(G, dim=3, seed=config.seed, weight="weight")

    # Node metrics (pulse)
    vol = win.std().replace([np.inf, -np.inf], np.nan)
    last_r = win.iloc[-1].replace([np.inf, -np.inf], np.nan)

    node_x, node_y, node_z = [], [], []
    node_text, node_color, node_size = [], [], []

    def _scale_size(v: float) -> float:
        # map volatility to marker size range
        if np.isnan(v):
            return 10.0
        return float(np.clip(10 + 2200 * abs(v), 10, 42))

    for n in G.nodes():
        x, y, z = pos[n]
        node_x.append(float(x))
        node_y.append(float(y))
        node_z.append(float(z))
        r = float(last_r.get(n, np.nan))
        v = float(vol.get(n, np.nan))
        node_color.append(r)
        node_size.append(_scale_size(v))
        node_text.append(f"{n}<br>last return: {r:+.3%}<br>vol: {v:.3%}")

    # Edge traces (as many segments)
    edge_x, edge_y, edge_z, edge_color = [], [], [], []
    for a, b, w in edges:
        x0, y0, z0 = pos[a]
        x1, y1, z1 = pos[b]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z1, None]
        edge_color.append(w)

    # Plotly can't color each line segment individually in one Scatter3d reliably,
    # so we split into two traces: positive and negative correlations.
    pos_x, pos_y, pos_z = [], [], []
    neg_x, neg_y, neg_z = [], [], []
    for a, b, w in edges:
        x0, y0, z0 = pos[a]
        x1, y1, z1 = pos[b]
        if w >= 0:
            pos_x += [x0, x1, None]
            pos_y += [y0, y1, None]
            pos_z += [z0, z1, None]
        else:
            neg_x += [x0, x1, None]
            neg_y += [y0, y1, None]
            neg_z += [z0, z1, None]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=pos_x,
            y=pos_y,
            z=pos_z,
            mode="lines",
            line=dict(color="rgba(0,200,100,0.35)", width=4),
            hoverinfo="skip",
            name="positive corr",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=neg_x,
            y=neg_y,
            z=neg_z,
            mode="lines",
            line=dict(color="rgba(220,60,60,0.35)", width=4),
            hoverinfo="skip",
            name="negative corr",
        )
    )
    fig.add_trace(
        go.Scatter3d(
            x=node_x,
            y=node_y,
            z=node_z,
            mode="markers+text",
            text=list(G.nodes()),
            textposition="top center",
            marker=dict(
                size=node_size,
                color=node_color,
                colorscale="RdYlGn",
                reversescale=False,
                cmin=-0.02,
                cmax=0.02,
                colorbar=dict(title="last return"),
                line=dict(width=0.5, color="rgba(255,255,255,0.35)"),
                opacity=0.92,
            ),
            hovertext=node_text,
            hoverinfo="text",
            name="coins",
        )
    )

    end_ts = rets.index[end_idx]
    if isinstance(end_ts, (pd.Timestamp, datetime)):
        end_label = str(end_ts)
    else:
        end_label = repr(end_ts)

    fig.update_layout(
        title=f"Pulse Network (3D) — window={config.window} @ {end_label}",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
    )

    meta = {
        "prices": prices,
        "returns": rets,
        "window_returns": win,
        "corr": corr,
        "edges": edges,
        "frame_end_index": end_idx,
    }
    return fig, meta

