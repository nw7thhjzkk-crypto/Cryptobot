import pandas as pd
import json
import logging
from typing import Dict, Any
import google.generativeai as genai
from bot.agents.base import BaseAgent
from bot.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

gemini_cache = {}

class GeminiContextAgent(BaseAgent):
    def __init__(self):
        super().__init__("GeminiContextAgent")
        self.is_configured = bool(GEMINI_API_KEY)
        if self.is_configured:
            genai.configure(api_key=GEMINI_API_KEY)

    def analyze(self, symbol: str, price_history: pd.DataFrame, quant_signals: list = None, **kwargs) -> Dict[str, Any]:
        if not self.is_configured:
            return self._create_hold_signal(symbol, "Gemini not configured")

        if len(price_history) < 10:
             return self._create_hold_signal(symbol, "Insufficient data for LLM analysis")

        last_date = str(price_history.index[-1])
        cache_key = f"{symbol}_{last_date}"

        if cache_key in gemini_cache:
            logger.info(f"Using cached Gemini analysis for {symbol}")
            return gemini_cache[cache_key]

        df = price_history.copy()

        recent_data = df.tail(5).to_dict(orient="records")

        quant_summary = []
        if quant_signals:
            for s in quant_signals:
                quant_summary.append({
                    "agent": s["agent"],
                    "signal": s["signal"],
                    "confidence": s["confidence"]
                })

        context = {
            "symbol": symbol,
            "recent_price_action": recent_data,
            "quant_signals": quant_summary
        }

        prompt = f"""
You are an adversarial financial analyst acting as a risk check.
Review the provided technical and quantitative data for {symbol}.
Identify potential risks, false breakouts, or macro conditions that might invalidate the quantitative signals.
Provide your output as a strictly formatted JSON object with no markdown wrappers or backticks.

Required schema:
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<string explaining your decision>",
  "risk_flags": ["<string>", ...],
  "supporting_factors": ["<string>", ...],
  "opposing_factors": ["<string>", ...]
}}

Context:
{json.dumps(context, indent=2)}
"""

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(
                 prompt,
                 generation_config={"response_mime_type": "application/json"}
            )

            raw_text = response.text.strip()

            data = json.loads(raw_text)

            signal_map = {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0}
            raw_signal = data.get("signal", "HOLD").upper()
            if raw_signal not in signal_map:
                raw_signal = "HOLD"

            confidence = min(max(float(data.get("confidence", 0.0)), 0.0), 1.0)
            score = signal_map[raw_signal] * confidence

            result = {
                "agent": self.name,
                "symbol": symbol,
                "signal": raw_signal,
                "score": score,
                "confidence": confidence,
                "reason": data.get("reasoning", "No reason provided"),
                "features": {
                    "risk_flags": data.get("risk_flags", []),
                    "supporting_factors": data.get("supporting_factors", []),
                    "opposing_factors": data.get("opposing_factors", [])
                }
            }

            gemini_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Gemini API failure for {symbol}: {e}")
            return self._create_hold_signal(symbol, f"Gemini API Error: {str(e)[:50]}")
