import os
import streamlit as st
import openai

def get_openai_client():
    if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
        return openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
    return None

def generate_alpha_strategy(description):
    """
    Takes a natural language description of market conditions or a hypothesis
    and asks the LLM to generate a Python trading strategy using VectorBT.
    """
    client = get_openai_client()
    if not client:
        return "Error: OpenAI API Key not found in .streamlit/secrets.toml"
        
    prompt = f"""
    You are a QuantEvolve expert factor-research agent generating an Alpha Strategy.
    The user's strategy concept is: "{description}"
    
    Please output a Python code block using the `vectorbt` library that implements this concept on a generic DataFrame (assume `df` has columns ['open', 'high', 'low', 'close', 'volume']). 
    Your code must:
    1. Cleanly define the indicators or conditions.
    2. Generate a boolean Series `entries` and `exits`.
    3. Include brief inline comments explaining the rationale.
    4. Only output the python code block, no other text.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Advanced model for best code generation
            messages=[
                {"role": "system", "content": "You are a quantitative developer code generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to OpenAI: {e}"
