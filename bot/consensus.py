import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

        self.weights = {
            "TrendAgent": 1.15,
            "MomentumAgent": 0.85,
            "MeanReversionAgent": 0.95,
            "BreakoutAgent": 0.95,
            "VolatilityAgent": 0.7,
            "VolumeAgent": 0.65,
            "RelativeStrengthAgent": 0.85,
            "GeminiContextAgent": 1.25
        }

    def aggregate_signals(self, symbol: str, quant_signals: List[Dict[str, Any]], regime_signal: Dict[str, Any], gemini_signal: Dict[str, Any] = None) -> Dict[str, Any]:

        total_score = 0.0
        total_weight = 0.0

        reasons = []
        buy_votes = 0
        sell_votes = 0

        all_signals = quant_signals.copy()
        if gemini_signal:
            all_signals.append(gemini_signal)

        regime = regime_signal.get("features", {}).get("regime", "sideways")

        # Regime-aware weight multipliers
        for sig in all_signals:
            agent_name = sig["agent"]
            signal = sig["signal"]
            score = sig["score"]
            base_weight = self.weights.get(agent_name, 1.0)

            # Boost / reduce based on regime
            weight = base_weight
            if "trending_bull" in regime or "trending" in regime:
                if agent_name in ("TrendAgent", "MomentumAgent", "BreakoutAgent", "RelativeStrengthAgent"):
                    weight *= 1.25
                if agent_name == "MeanReversionAgent":
                    weight *= 0.4
            elif "ranging" in regime:
                if agent_name == "MeanReversionAgent":
                    weight *= 1.35
                if agent_name in ("TrendAgent", "BreakoutAgent"):
                    weight *= 0.55
            elif "risk_off" in regime:
                weight *= 0.3  # heavily suppress in risk-off

            if signal == "BUY":
                buy_votes += 1
            elif signal == "SELL":
                sell_votes += 1

            total_score += (score * weight)
            total_weight += weight

            if signal != "HOLD":
                reasons.append(f"{agent_name}({signal}): {sig.get('reason', '')}")

        if total_weight == 0:
            return self._build_result(symbol, "HOLD", 0.0, 0.0, "No agents returned valid signals", regime)

        consensus_score = total_score / total_weight

        # Hard regime overrides
        if "risk_off" in regime:
            logger.warning(f"Consensus [{symbol}]: risk_off regime → suppress new buys")
            if consensus_score > 0:
                consensus_score = min(consensus_score, 0.0)
                reasons.append("BUY suppressed due to risk_off regime")

        if "trending_bull" in regime and consensus_score < 0:
            consensus_score *= 0.55
            reasons.append("SELL weakened by trending_bull regime")

        if "trending_bear" in regime and consensus_score > 0:
            consensus_score *= 0.55
            reasons.append("BUY weakened by trending_bear regime")

        final_signal = "HOLD"
        confidence = abs(consensus_score)

        if consensus_score > 0 and confidence >= self.min_confidence:
            final_signal = "BUY"
        elif consensus_score < 0 and confidence >= self.min_confidence:
            final_signal = "SELL"

        # Conflict penalty
        if buy_votes > 0 and sell_votes > 0:
            conflict_penalty = 0.18 * min(buy_votes, sell_votes)
            confidence = max(0.0, confidence - conflict_penalty)
            reasons.append(f"Conflict penalty ({buy_votes}B/{sell_votes}S)")
            if confidence < self.min_confidence:
                final_signal = "HOLD"

        # Gemini veto (high confidence only)
        if gemini_signal and gemini_signal.get("signal") != "HOLD":
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
