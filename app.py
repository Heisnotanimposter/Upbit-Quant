import streamlit as st

st.set_page_config(
    page_title="UPbit QuantEvolve",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📈 UPbit QuantEvolve Platform")
    st.markdown("""
    Welcome to the **UPbit QuantEvolve** platform. 
    This application modernizes cryptocurrency quantitative trading through:
    
    *   **Data & Signal Engines**: Real-time market data monitoring utilizing `ccxt`.
    *   **AI Strategy Agent**: Discovery, ideation, and generation of strategies via LLM.
    *   **Backtesting & Simulation**: Thorough performance evaluation before live deployments.
    *   **Live OMS & Wallet**: Direct connection to your UPbit Wallet for automated real-time execution.
    
    👈 Please select a module from the sidebar to begin.
    """)
    
    with st.expander("System Architecture Overview"):
        st.markdown("""
        **Data Engine** fetches robust OLHCV data via public exchange APIs.
        **Strategy Engine** passes narrative prompts to an LLM mapping raw data into weighted Alpha Factors.
        **Order Management** handles position sizing through dynamic weighted gating, mitigating downside risk with Stop Losses and sending REST API executions directly to UPbit via user secrets.
        """)

if __name__ == "__main__":
    main()
