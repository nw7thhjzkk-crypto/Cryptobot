import pandas as pd
import json
import logging
from typing import Dict, Any, List
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
            try:
                genai.configure(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")
                self.is_configured = False

    def analyze(self, symbol: str, price_history: pd.DataFrame, quant_signals: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        if not self.is_configured:
            return self._create_hold_signal(symbol, "Gemini not configured (set GEMINI_API_KEY)")

        if len(price_history) < 10:
            return self._create_hold_signal(symbol, "Insufficient data for LLM analysis")

        # Simple cache keyed by symbol + last bar timestamp
        last_date = str(price_history.index[-1])
        cache_key = f"{symbol}_{last_date}"
        if cache_key in gemini_cache:
            return gemini_cache[cache_key]

        df = price_history.copy()
        recent = df.tail(8)

        # Compact summary for the prompt
        price_summary = {
            "last_close": float(recent["close"].iloc[-1]),
            "change_5d_pct": float((recent["close"].iloc[-1] / recent["close"].iloc[0] - 1) * 100) if len(recent) > 1 else 0,
            "high_8d": float(recent["high"].max()),
            "low_8d": float(recent["low"].min()),
        }

        quant_summary = []
        if quant_signals:
            for s in quant_signals:
                quant_summary.append({
                    "agent": s.get("agent"),
                    "signal": s.get("signal"),
                    "confidence": round(float(s.get("confidence", 0)), 2),
                    "reason": str(s.get("reason", ""))[:80]
                })

        prompt = f"""You are a senior risk manager reviewing a trading signal for {symbol}.
Your job is to act as an adversarial check against the quantitative agents.

Price context:
{json.dumps(price_summary, indent=2)}

Quantitative agent signals:
{json.dumps(quant_summary, indent=2)}

Decide whether the overall bias should be BUY, SELL, or HOLD.
Be conservative. Prefer HOLD when evidence is mixed or risk is elevated.

Return ONLY valid JSON with this exact schema (no markdown):
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0 to 1.0,
  "reasoning": "one concise sentence",
  "risk_flags": ["list of short risk notes"]
}}
"""

        try:
            model = genai.GenerativeModel(GEMINI_MODEL or "gemini-2.0-flash")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            raw = response.text.strip()
            data = json.loads(raw)

            raw_signal = str(data.get("signal", "HOLD")).upper()
            if raw_signal not in ("BUY", "SELL", "HOLD"):
                raw_signal = "HOLD"

            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))

            score = confidence if raw_signal == "BUY" else (-confidence if raw_signal == "SELL" else 0.0)

            result = {
                "agent": self.name,
                "symbol": symbol,
                "signal": raw_signal,
                "score": score,
                "confidence": confidence,
                "reason": data.get("reasoning", "No reason provided")[:200],
                "features": {
                    "risk_flags": data.get("risk_flags", [])
                }
            }

            gemini_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Gemini API failure for {symbol}: {e}")
            return self._create_hold_signal(symbol, f"Gemini error: {str(e)[:60]}")
