import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConsensusEngine:
    def __init__(self, attribution_tracker=None):
        # We can dynamically adjust strategy weights based on performance if attribution is provided
        self.attribution_tracker = attribution_tracker
        self.regime_multipliers = {
            "trending_bull": {"trend": 1.5, "breakout": 1.5, "momentum": 1.2, "mean_reversion": 0.0},
            "trending_bear": {"trend": 1.5, "breakout": 1.5, "momentum": 1.2, "mean_reversion": 0.0},
            "ranging": {"trend": 0.0, "breakout": 0.5, "momentum": 0.5, "mean_reversion": 2.0},
            "high_volatility": {"trend": 0.5, "breakout": 0.5, "momentum": 0.5, "mean_reversion": 0.5, "volatility": 2.0},
            "risk_off": {"trend": 0.1, "breakout": 0.1, "momentum": 0.1, "mean_reversion": 0.1},
            "transitional": {"trend": 1.0, "breakout": 1.0, "momentum": 1.0, "mean_reversion": 1.0},
            "unknown": {"trend": 1.0, "breakout": 1.0, "momentum": 1.0, "mean_reversion": 1.0}
        }

    def _get_agent_category(self, agent_name: str) -> str:
        name_lower = agent_name.lower()
        if "trend" in name_lower or "donchian" in name_lower or "dualmomentum" in name_lower:
            return "trend"
        if "breakout" in name_lower or "rangeexpansion" in name_lower:
            return "breakout"
        if "reversion" in name_lower:
            return "mean_reversion"
        if "volatility" in name_lower:
            return "volatility"
        if "momentum" in name_lower or "relativestrength" in name_lower:
            return "momentum"
        return "trend"  # default

    def aggregate_signals(
        self,
        symbol: str,
        quant_signals: List[Dict[str, Any]],
        regime_signal: Dict[str, Any],
        gemini_signal: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        regime = regime_signal.get("regime", "unknown")
        if isinstance(regime_signal.get("features"), dict):
             regime = regime_signal["features"].get("regime", regime)

        # Fallback for missing/invalid regime
        if regime not in self.regime_multipliers:
             regime = "unknown"

        regime_confidence = regime_signal.get("confidence", 0.5)

        multipliers = self.regime_multipliers.get(regime, self.regime_multipliers["unknown"])

        total_score = 0.0
        total_weight = 0.0
        primary_agent = "none"
        highest_weighted_score = 0.0

        for sig in quant_signals:
            if sig["signal"] == "HOLD":
                continue

            agent_name = sig["agent"]
            base_score = sig.get("score", 0.0)
            confidence = sig.get("confidence", 0.5)

            category = self._get_agent_category(agent_name)
            regime_mult = multipliers.get(category, 1.0)

            # HARD GATE: Check regime compatibility
            # If the strategy strictly declares regimes, and current is not one of them, BLOCK IT.
            is_compatible = True
            if "regime_compatibility" in sig and sig["regime_compatibility"]:
                 if regime not in sig["regime_compatibility"]:
                      is_compatible = False

            # If regime is completely unknown, we must be conservative. Only strategies compatible with "unknown" can trade.
            # Most shouldn't be, so they get blocked.
            if regime == "unknown" and ("regime_compatibility" in sig and sig["regime_compatibility"]):
                 if "unknown" not in sig["regime_compatibility"]:
                      is_compatible = False

            # Low confidence regime fallback
            if regime_confidence < 0.3:
                 # If we aren't confident in the regime, it acts like unknown.
                 if "unknown" not in sig.get("regime_compatibility", []):
                     is_compatible = False

            if not is_compatible:
                logger.debug(f"Strategy {agent_name} explicitly blocked via multiplier 0.0 due to strict regime gate: {regime}")
                regime_mult = 0.0

            # Even if regime multiplier is zero from dictionary, ensure the hard gate holds
            if regime_mult == 0.0:
                 continue

            perf_mult = 1.0
            if self.attribution_tracker:
                 perf_mult = self.attribution_tracker.get_strategy_weight(agent_name)

            final_weight = regime_mult * perf_mult * confidence
            weighted_score = base_score * final_weight

            total_score += weighted_score
            total_weight += final_weight

            if abs(weighted_score) > abs(highest_weighted_score) and regime_mult > 0.0:
                highest_weighted_score = weighted_score
                primary_agent = agent_name

        # Avoid div by zero
        normalized_score = total_score / total_weight if total_weight > 0 else 0.0

        # Gemini can act as a veto, not a direct trader
        if gemini_signal and gemini_signal.get("signal") == "VETO":
             logger.warning(f"Gemini AI VETO applied for {symbol}. Reason: {gemini_signal.get('reason')}")
             return {
                 "symbol": symbol,
                 "signal": "HOLD",
                 "score": 0.0,
                 "confidence": 1.0,
                 "reason": f"AI Veto: {gemini_signal.get('reason')}",
                 "primary_agent": "gemini_veto"
             }

        # Threshold for action
        final_signal = "HOLD"
        confidence_out = min(abs(normalized_score), 1.0)

        if normalized_score > 0.35:
            final_signal = "BUY"
        elif normalized_score < -0.35:
            final_signal = "SELL"

        return {
            "symbol": symbol,
            "signal": final_signal,
            "score": normalized_score,
            "confidence": confidence_out,
            "reason": f"Regime: {regime}, Aggregate Score: {normalized_score:.2f}",
            "primary_agent": primary_agent
        }
