import os
import streamlit as st

def generate_freqtrade_strategy_file(strategy_name, strategy_logic_code):
    """
    Wraps the provided AI logic into a Freqtrade Strategy class template.
    Returns the string representing the full freqtrade-compatible python file.
    """
    template = f"""
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class {strategy_name}(IStrategy):
    \"\"\"
    Auto-generated Strategy via UPbit-Quant AI Agent.
    \"\"\"
    # Strategy parameters
    minimal_roi = {{
        "0": 0.1
    }}
    stoploss = -0.10
    timeframe = '1h'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Original logic might need adaptation to freqtrade's ta-lib style
        # This is a boilerplate holder for the AI logic.
        {strategy_logic_code or "# Define your indicators here"}
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # Insert entry conditions here based on indicators
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # Insert exit conditions here
            ),
            'exit_long'] = 1
        return dataframe
"""
    return template

def export_as_downloadable(content, filename="user_strategy.py"):
    """
    Helper to provide the content as a downloadable element in Streamlit.
    (This logic would be used in the UI).
    """
    st.download_button(
        label=f"💾 Download {filename} for Freqtrade",
        data=content,
        file_name=filename,
        mime="text/x-python"
    )
