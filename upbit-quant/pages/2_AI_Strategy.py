import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agents.strategy_agent import generate_alpha_strategy

st.set_page_config(page_title="QuantEvolve - AI Strategy Discovery", page_icon="🧠", layout="wide")
st.title("🧠 AI-Driven Strategy Discovery (QuantEvolve)")

st.markdown("""
This module uses a Large Language Model (LLM) to discover and formulate Alpha factors.
Describe your hypothesis or the market anomaly you wish to exploit, and the LLM will generate a complete Python Strategy boilerplate utilizing **VectorBT** for you to copy and backtest in the next module.
""")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Strategy Description (Narrative Alpha)")
    user_prompt = st.text_area(
        "Describe your trading idea:", 
        height=200, 
        placeholder="e.g. Generate a mean-reverting strategy using Bollinger Bands: Buy when price crosses below lower band, Sell when price crosses above upper band. Add an RSI filter > 30 for buying to avoid deep oversold cascades."
    )
    
    if st.button("Generate Strategy Code", type="primary"):
        with st.spinner("LLM is developing strategy logic... Please wait."):
            code_result = generate_alpha_strategy(user_prompt)
            st.session_state['generated_strategy'] = code_result
            st.success("Strategy generated successfully!")

with col2:
    st.subheader("Implementation Code")
    if 'generated_strategy' in st.session_state:
        st.code(st.session_state['generated_strategy'], language="python")
    else:
        st.info("Your AI-generated Python code will appear here.")
        
st.divider()

st.markdown("""
### How it works:
1. **Factor Generation**: Translates natural language alpha concepts into programmatic features.
2. **Formulaic Mutation**: Generates logic optimized for robustness instead of overfitting.
3. **Evaluation Loop**: (Coming soon) Automatically passes generated code to the backtester and uses the QuantStats report as feedback to iteratively refine the strategy prompt!
""")
