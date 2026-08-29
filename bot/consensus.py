import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

        self.weights = {
            "TrendAgent": 1.0,
            "MomentumAgent": 0.8,
            "MeanReversionAgent": 0.9,
            "BreakoutAgent": 0.9,
            "VolatilityAgent": 0.7,
            "VolumeAgent": 0.6,
            "RelativeStrengthAgent": 0.8,
            "GeminiContextAgent": 1.2
        }

    def aggregate_signals(self, symbol: str, quant_signals: List[Dict[str, Any]], regime_signal: Dict[str, Any], gemini_signal: Dict[str, Any] = None) -> Dict[str, Any]:

        total_score = 0.0
        total_weight = 0.0

        reasons = []
        buy_votes = 0
        sell_votes = 0
        hold_votes = 0

        all_signals = quant_signals.copy()
        if gemini_signal:
            all_signals.append(gemini_signal)

        for sig in all_signals:
            agent_name = sig["agent"]
            signal = sig["signal"]
            score = sig["score"]
            weight = self.weights.get(agent_name, 1.0)

            if signal == "BUY":
                buy_votes += 1
            elif signal == "SELL":
                sell_votes += 1
            else:
                hold_votes += 1

            total_score += (score * weight)
            total_weight += weight

            if signal != "HOLD":
                reasons.append(f"{agent_name}({signal}): {sig['reason']}")

        if total_weight == 0:
             return self._build_result(symbol, "HOLD", 0.0, 0.0, "No agents returned valid signals", "unknown")

        consensus_score = total_score / total_weight

        regime = regime_signal["features"].get("regime", "sideways")

        if regime == "risk-off":
            logger.warning(f"Consensus [{symbol}]: Regime is risk-off. Forcing HOLD/SELL behavior.")
            if consensus_score > 0:
                consensus_score = 0.0
                reasons.append("Suppressed BUY due to risk-off regime")

        elif regime == "bullish" and consensus_score < 0:
            consensus_score *= 0.5
            reasons.append("Weakened SELL due to bullish regime")

        elif regime == "bearish" and consensus_score > 0:
            consensus_score *= 0.5
            reasons.append("Weakened BUY due to bearish regime")

        final_signal = "HOLD"
        confidence = abs(consensus_score)

        if consensus_score > 0 and confidence >= self.min_confidence:
            final_signal = "BUY"
        elif consensus_score < 0 and confidence >= self.min_confidence:
            final_signal = "SELL"

        if buy_votes > 0 and sell_votes > 0:
            conflict_penalty = 0.2 * min(buy_votes, sell_votes)
            confidence = max(0.0, confidence - conflict_penalty)
            reasons.append(f"Confidence reduced due to signal conflict ({buy_votes} Buy, {sell_votes} Sell)")
            if confidence < self.min_confidence:
                 final_signal = "HOLD"

        if gemini_signal and gemini_signal["signal"] != "HOLD":
            if final_signal == "BUY" and gemini_signal["signal"] == "SELL" and gemini_signal["confidence"] > 0.6:
                final_signal = "HOLD"
                confidence = 0.0
                reasons.append(f"Vetoed by Gemini: {gemini_signal['reason']}")
            elif final_signal == "SELL" and gemini_signal["signal"] == "BUY" and gemini_signal["confidence"] > 0.6:
                final_signal = "HOLD"
                confidence = 0.0
                reasons.append(f"Vetoed by Gemini: {gemini_signal['reason']}")

        reason_str = " | ".join(reasons) if reasons else "Neutral consensus"

        return self._build_result(symbol, final_signal, consensus_score, confidence, reason_str, regime)

    def _build_result(self, symbol: str, signal: str, score: float, confidence: float, reason: str, regime: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "signal": signal,
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "regime": regime
        }
