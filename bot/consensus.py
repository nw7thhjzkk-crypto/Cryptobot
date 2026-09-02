import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

        self.weights = {
            "TrendAgent": 1.15,
            "MomentumAgent": 0.95,
            "MeanReversionAgent": 0.95,
            "BreakoutAgent": 1.0,
            "VolatilityAgent": 0.7,
            "VolumeAgent": 0.7,
            "RelativeStrengthAgent": 0.9,
            "GeminiContextAgent": 1.2
        }

    def aggregate_signals(self, symbol: str, quant_signals: List[Dict[str, Any]], regime_signal: Dict[str, Any], gemini_signal: Dict[str, Any] = None) -> Dict[str, Any]:

        total_score = 0.0
        total_weight = 0.0
        reasons = []
        buy_votes = 0
        sell_votes = 0
        active_agents = 0

        all_signals = quant_signals.copy()
        if gemini_signal:
            all_signals.append(gemini_signal)

        regime = regime_signal.get("features", {}).get("regime", "sideways")

        for sig in all_signals:
            agent_name = sig["agent"]
            signal = sig.get("signal", "HOLD")
            score = float(sig.get("score", 0) or 0)
            base_weight = self.weights.get(agent_name, 1.0)

            weight = base_weight
            if "trending_bull" in regime or regime == "trending":
                if agent_name in ("TrendAgent", "MomentumAgent", "BreakoutAgent", "RelativeStrengthAgent"):
                    weight *= 1.3
                if agent_name == "MeanReversionAgent":
                    weight *= 0.35
            elif "ranging" in regime:
                if agent_name == "MeanReversionAgent":
                    weight *= 1.4
                if agent_name in ("TrendAgent", "BreakoutAgent"):
                    weight *= 0.5
            elif "risk_off" in regime:
                weight *= 0.25

            # Only active (non-HOLD) signals contribute to score
            if signal == "HOLD":
                continue

            active_agents += 1
            if signal == "BUY":
                buy_votes += 1
            elif signal == "SELL":
                sell_votes += 1

            total_score += score * weight
            total_weight += weight
            reasons.append(f"{agent_name}({signal}): {sig.get('reason', '')}")

        if total_weight == 0 or active_agents == 0:
            return self._build_result(symbol, "HOLD", 0.0, 0.0, "No active agent signals", regime)

        consensus_score = total_score / total_weight

        if "risk_off" in regime and consensus_score > 0:
            consensus_score = min(consensus_score, 0.0)
            reasons.append("BUY suppressed due to risk_off regime")

        if "trending_bull" in regime and consensus_score < 0:
            consensus_score *= 0.5
            reasons.append("SELL weakened by trending_bull regime")

        if "trending_bear" in regime and consensus_score > 0:
            consensus_score *= 0.5
            reasons.append("BUY weakened by trending_bear regime")

        confidence = abs(consensus_score)
        # Boost confidence when multiple agents agree in same direction
        if buy_votes >= 2 and sell_votes == 0:
            confidence = min(confidence * (1.0 + 0.12 * (buy_votes - 1)), 0.98)
        if sell_votes >= 2 and buy_votes == 0:
            confidence = min(confidence * (1.0 + 0.12 * (sell_votes - 1)), 0.98)

        final_signal = "HOLD"
        if consensus_score > 0 and confidence >= self.min_confidence:
            final_signal = "BUY"
        elif consensus_score < 0 and confidence >= self.min_confidence:
            final_signal = "SELL"

        if buy_votes > 0 and sell_votes > 0:
            conflict_penalty = 0.15 * min(buy_votes, sell_votes)
            confidence = max(0.0, confidence - conflict_penalty)
            reasons.append(f"Conflict penalty ({buy_votes}B/{sell_votes}S)")
            if confidence < self.min_confidence:
                final_signal = "HOLD"

        if gemini_signal and gemini_signal.get("signal") not in (None, "HOLD"):
            g_conf = gemini_signal.get("confidence", 0)
            if final_signal == "BUY" and gemini_signal["signal"] == "SELL" and g_conf > 0.65:
                final_signal = "HOLD"
                confidence = 0.0
                reasons.append(f"Gemini veto: {gemini_signal.get('reason', '')}")
            elif final_signal == "SELL" and gemini_signal["signal"] == "BUY" and g_conf > 0.65:
                final_signal = "HOLD"
                confidence = 0.0
                reasons.append(f"Gemini veto: {gemini_signal.get('reason', '')}")

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
