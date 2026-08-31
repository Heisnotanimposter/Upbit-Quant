import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("Visualizer")

class BacktestVisualizer:
    """
    Generates interactive HTML visualization dashboards for backtesting analysis.
    Renders multi-strategy equity curves, drawdown underwater charts, and performance tables.
    """

    @staticmethod
    def generate_html_report(results: Dict[str, Any], df: pd.DataFrame, output_path: str = "backtest_results.html"):
        """
        Builds a comprehensive interactive HTML dashboard.
        """
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(
                "📈 Multi-Strategy Portfolio Equity Curve Comparison (KRW)",
                "📉 Drawdown Underwater Chart (%)",
                "📊 Price Action & Trade Execution Reference"
            )
        )

        colors = {
            "RL_Agent": "#00E676",               # Neon Green
            "High_Turnover_Scalping": "#00B0FF", # Vivid Cyan
            "Volatility_Breakout": "#FF9100",    # Deep Orange
            "Buy_and_Hold": "#B0BEC5"            # Light Grey
        }

        # 1. Equity Curves
        for name, data in results.items():
            if "equity_curve" in data:
                eq = data["equity_curve"]
                steps = list(range(len(eq)))
                fig.add_trace(
                    go.Scatter(
                        x=steps,
                        y=eq,
                        mode="lines",
                        name=f"{name} ({data.get('total_return_pct', 0):+.2f}%)",
                        line=dict(color=colors.get(name, "#FFFFFF"), width=2)
                    ),
                    row=1, col=1
                )

        # 2. Drawdown Curves
        for name, data in results.items():
            if "equity_curve" in data:
                eq = np.array(data["equity_curve"])
                peaks = np.maximum.accumulate(eq)
                dd = ((peaks - eq) / peaks) * -100.0
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(dd))),
                        y=dd,
                        mode="lines",
                        name=f"{name} DD",
                        line=dict(color=colors.get(name, "#FFFFFF"), width=1.5),
                        showlegend=False
                    ),
                    row=2, col=1
                )

        # 3. Price Chart
        if not df.empty:
            prices = df["close"].values
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(prices))),
                    y=prices,
                    mode="lines",
                    name="Asset Close Price (KRW)",
                    line=dict(color="#FFD700", width=1.5)
                ),
                row=3, col=1
            )

        fig.update_layout(
            template="plotly_dark",
            title=dict(
                text="⚡ Bithumb Quant Backtest Simulation Dashboard",
                font=dict(size=20, color="#FFFFFF")
            ),
            hovermode="x unified",
            height=900,
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_yaxes(title_text="Portfolio Value (KRW)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        fig.update_yaxes(title_text="Price (KRW)", row=3, col=1)

        # Build Metrics Summary Table HTML
        table_rows = ""
        for name, data in results.items():
            ret = data.get("total_return_pct", 0)
            color_ret = "#00E676" if ret >= 0 else "#FF5252"
            table_rows += f"""
            <tr>
                <td style="padding:10px;font-weight:bold;color:{colors.get(name, '#FFF')}">{name}</td>
                <td style="padding:10px;color:{color_ret};font-weight:bold">{ret:+.2f}%</td>
                <td style="padding:10px;color:#FF5252">-{data.get('max_drawdown_pct', 0):.2f}%</td>
                <td style="padding:10px">{data.get('sharpe_ratio', 0):.2f}</td>
                <td style="padding:10px">{data.get('sortino_ratio', 0):.2f}</td>
                <td style="padding:10px">{data.get('win_rate_pct', 0):.1f}%</td>
                <td style="padding:10px">{data.get('profit_factor', 0):.2f}</td>
                <td style="padding:10px">{data.get('total_trades', 0)}</td>
                <td style="padding:10px">{data.get('turnover_multiplier', 0):.1f}x</td>
                <td style="padding:10px">{data.get('total_fees_paid_krw', 0):,.0f} KRW</td>
            </tr>
            """

        table_html = f"""
        <div style="margin:20px 40px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif;color:#ECEFF1;">
            <h2 style="color:#00E676;border-bottom:1px solid #37474F;padding-bottom:8px;">📊 Performance Summary Ledger</h2>
            <table style="width:100%;border-collapse:collapse;text-align:left;background:#1E293B;border-radius:8px;overflow:hidden;">
                <thead>
                    <tr style="background:#0F172A;color:#94A3B8;font-size:13px;text-transform:uppercase;">
                        <th style="padding:12px 10px;">Strategy Model</th>
                        <th style="padding:12px 10px;">Total Return</th>
                        <th style="padding:12px 10px;">Max Drawdown</th>
                        <th style="padding:12px 10px;">Sharpe</th>
                        <th style="padding:12px 10px;">Sortino</th>
                        <th style="padding:12px 10px;">Win Rate</th>
                        <th style="padding:12px 10px;">Profit Factor</th>
                        <th style="padding:12px 10px;">Trades</th>
                        <th style="padding:12px 10px;">Seed Turnover</th>
                        <th style="padding:12px 10px;">Total Fees</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """

        # Save HTML
        raw_plot_html = fig.to_html(include_plotlyjs="cdn", full_html=False)
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Bithumb Quant Backtest Report</title>
            <style>body {{ background: #0B0F19; margin:0; padding: 20px; }}</style>
        </head>
        <body>
            {table_html}
            <div style="margin: 0 20px;">
                {raw_plot_html}
            </div>
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        logger.info(f"🎉 Generated interactive backtest HTML report: {output_path}")
        return output_path
