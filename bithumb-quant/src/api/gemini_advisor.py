import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("GeminiAdvisor")

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai package not installed. Gemini AI Advisor will run in fallback mode.")

class GeminiAdvisor:
    """
    Google AI Studio (Gemini 2.5 Flash / Pro) integration for market regime analysis.
    Evaluates crypto market conditions and outputs risk parameters for the trading engine.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None

        if self.api_key and GENAI_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Gemini Advisor using model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
        else:
            logger.info("Gemini API Key missing or google-genai unavailable. Operating in deterministic fallback mode.")

    def evaluate_market_regime(self, market_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends aggregated market data to Gemini and returns structured regime & risk guidance.
        """
        fallback_response = {
            "regime": "NEUTRAL",
            "risk_level": "NEUTRAL",
            "position_multiplier": 1.0,
            "reasoning": "Using deterministic fallback (Gemini API inactive or unreachable)."
        }

        if not self.client:
            return fallback_response

        prompt = f"""
You are an expert quantitative crypto risk manager analyzing the Bithumb KRW market.
Below is the current market metrics summary for target coins:

{json.dumps(market_summary, indent=2)}

Task:
Analyze the price trends, volatility, and volume indicators.
Classify the overall market regime and determine the recommended risk exposure multiplier.

Return ONLY a single valid JSON object adhering to this schema:
{{
    "regime": "BULL_TREND" | "BEAR_TREND" | "CHOPPY" | "HIGH_VOLATILITY_RISK",
    "risk_level": "AGGRESSIVE" | "NEUTRAL" | "CONSERVATIVE" | "HALT",
    "position_multiplier": float (number between 0.0 and 1.0),
    "reasoning": "Concise 1-2 sentence market analysis"
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            result = json.loads(response.text)
            logger.info(f"Gemini Regime Assessment: {result.get('regime')} | Multiplier: {result.get('position_multiplier')}")
            return result
        except Exception as e:
            logger.error(f"Gemini API error during regime evaluation: {e}")
            return fallback_response

    def generate_daily_report(self, portfolio_summary: Dict[str, Any]) -> str:
        """
        Generates a readable daily trade summary formatted for Telegram broadcast.
        """
        if not self.client:
            return f"📊 *Daily Summary (Deterministic)*\nTotal Balance: {portfolio_summary.get('total_krw', 0):,.0f} KRW\nOpen Positions: {portfolio_summary.get('open_positions_count', 0)}"

        prompt = f"""
Create a concise, professional daily trading report formatted in Telegram Markdown.
Portfolio Details:
{json.dumps(portfolio_summary, indent=2)}

Include key metrics: Total Equity, Daily PnL (%), Active Positions, Win/Loss Record, and 1 sentence AI outlook.
Keep it clean with emoji bullet points.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4)
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error generating daily report: {e}")
            return f"📊 *Daily Trading Report*\nTotal Balance: {portfolio_summary.get('total_krw', 0):,.0f} KRW"
