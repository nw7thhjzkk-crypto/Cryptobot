import logging
import pandas as pd
import json
import os
from datetime import datetime, timezone
import google.generativeai as genai
from bot.config import GEMINI_API_KEY, GEMINI_MODEL
from bot.research.validator import WalkForwardValidator
from bot.agents.donchian import DonchianBreakoutAgent
from bot.agents.dual_momentum import DualMomentumAgent
from bot.agents.range_expansion import RangeExpansionAgent
from bot.broker import get_price_history_batch

logger = logging.getLogger(__name__)

class EvolutionEngine:
    """
    Controlled AI Strategy Evolution.
    Analyzes current performance, queries Gemini for hypothesis generation,
    then executes a strictly sandboxed out-of-sample backtest.
    """
    def __init__(self):
        self.is_configured = bool(GEMINI_API_KEY)
        if self.is_configured:
            genai.configure(api_key=GEMINI_API_KEY)

    def generate_hypothesis(self, strategy_description: str, performance_report: dict):
        if not self.is_configured:
            logger.warning("Gemini API not configured. Returning deterministic placeholder for testing/dry-run.")
            return {
                "proposed_parameters": {"entry_lookback": 25, "exit_lookback": 15},
                "hypothesis": "Increasing lookback provides a more stable breakout threshold during high noise regimes.",
                "expected_outcome": "Reduced whipsaws and slightly higher win rate."
            }

        prompt = f"""
You are an expert quantitative researcher.
A strategy described as follows:
{strategy_description}

Has produced the following out-of-sample performance:
{json.dumps(performance_report, indent=2)}

Propose exactly ONE set of parameter changes to improve its robustness and out of sample performance.
For example, modifying a lookback window, threshold, or multiplier.

Respond ONLY with valid JSON in this schema (no markdown):
{{
  "proposed_parameters": {{ "param1": 10, "param2": 2.5 }},
  "hypothesis": "Why you think this will improve performance.",
  "expected_outcome": "Less drawdown, higher win rate, etc."
}}
"""
        model_name = GEMINI_MODEL if GEMINI_MODEL else "gemini-1.5-flash"
        if model_name in ("gemini-3.6-flash", "gemini-pro"):
            model_name = "gemini-1.5-flash"

        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw = response.text.strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Evolution hypothesis generation failed: {e}")
            return None

    def evaluate_hypothesis(self, agent_class, symbol: str, data: pd.DataFrame, hypothesis_params: dict):
        """
        Instantiates the agent with the new params and runs it through WalkForwardValidator.
        Returns the report.
        """
        try:
            agent = agent_class(**hypothesis_params)
            validator = WalkForwardValidator()
            report = validator.validate(agent, symbol, data)
            return report
        except Exception as e:
             logger.error(f"Failed to evaluate hypothesis: {e}")
             return None

    def create_markdown_report(self, agent_name, baseline_report, hypothesis, hypothesis_report, passed, rejection_reason):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        decision = "ACCEPTED" if passed else "REJECTED"

        report = f"""# Strategy Evolution Report: {agent_name}
**Date:** {timestamp}
**Decision:** {decision}

## Baseline Performance
- **Train Return:** {baseline_report['train']['total_return']:.2%}
- **Val Return:** {baseline_report['validate']['total_return']:.2%}
- **Val Sharpe:** {baseline_report['validate'].get('sharpe_ratio', 0.0):.2f}
- **Val Max Drawdown:** {baseline_report['validate']['max_drawdown']:.2%}
- **Robustness Passed:** {baseline_report.get('robustness', {}).get('passed', False)}

## AI Hypothesis
- **Hypothesis:** {hypothesis.get('hypothesis', 'N/A')}
- **Proposed Parameters:** {json.dumps(hypothesis.get('proposed_parameters', {}))}
- **Expected Outcome:** {hypothesis.get('expected_outcome', 'N/A')}

## Hypothesis Validation
- **Train Return:** {hypothesis_report['train']['total_return']:.2%}
- **Val Return:** {hypothesis_report['validate']['total_return']:.2%}
- **Val Sharpe:** {hypothesis_report['validate'].get('sharpe_ratio', 0.0):.2f}
- **Val Max Drawdown:** {hypothesis_report['validate']['max_drawdown']:.2%}
- **Val Win Rate:** {hypothesis_report['validate']['win_rate']:.2%}
- **Val Trade Count:** {hypothesis_report['validate']['num_trades']}
- **Robustness Passed:** {hypothesis_report.get('robustness', {}).get('passed', False)}

## Conclusion
"""
        if not passed:
            report += f"The hypothesis was **REJECTED**.\nReason: {rejection_reason}\n"
        else:
            report += "The hypothesis was **ACCEPTED** for Candidate phase.\n"

        return report

def run_evolution_cycle():
    logger.info("Starting Strategy Evolution Cycle...")

    symbol = "BTC/USD"
    logger.info(f"Fetching historical data for {symbol}")

    res = get_price_history_batch([symbol], lookback_days=400)

    if not res["success"] or symbol not in res["data"]:
        logger.error("Failed to fetch historical data for evolution.")
        return

    df = res["data"][symbol]

    engine = EvolutionEngine()
    validator = WalkForwardValidator()

    logger.info("Evaluating Baseline DonchianBreakoutAgent...")
    baseline_agent = DonchianBreakoutAgent()
    baseline_report = validator.validate(baseline_agent, symbol, df)

    logger.info("Generating hypothesis...")
    desc = "DonchianBreakoutAgent uses a 20 period rolling max for entry and 10 period rolling min for exit."
    hypothesis = engine.generate_hypothesis(desc, baseline_report)

    if not hypothesis:
        logger.error("No hypothesis generated. Aborting cycle.")
        return

    logger.info(f"Hypothesis generated: {hypothesis}")

    new_params = hypothesis.get("proposed_parameters", {})
    safe_params = {k: v for k, v in new_params.items() if k in ["entry_lookback", "exit_lookback"]}

    if not safe_params:
        logger.error("No safe parameters proposed.")
        return

    logger.info(f"Evaluating hypothesis with params: {safe_params}")
    hypothesis_report = engine.evaluate_hypothesis(DonchianBreakoutAgent, symbol, df, safe_params)

    if not hypothesis_report:
        logger.error("Failed to evaluate hypothesis.")
        return

    passed = False
    rejection_reason = ""

    if not hypothesis_report["passed"]:
        rejection_reason = hypothesis_report.get("status", "Failed basic out-of-sample constraints")
    elif not hypothesis_report.get("robustness", {}).get("passed", False):
        rejection_reason = "Failed Monte Carlo robustness bootstrapping."
    elif hypothesis_report["validate"]["total_return"] <= baseline_report["validate"]["total_return"]:
        rejection_reason = "Out-of-sample return did not beat baseline."
    else:
        passed = True

    print("\n" + "="*50)
    print("EVOLUTION CYCLE SUMMARY")
    print("="*50)
    print(f"Agent: DonchianBreakoutAgent")
    print(f"Proposed Params: {safe_params}")
    print(f"Hypothesis: {hypothesis.get('hypothesis')}")
    print(f"Baseline Val Return: {baseline_report['validate']['total_return']:.2%}")
    print(f"Hypothesis Val Return: {hypothesis_report['validate']['total_return']:.2%}")
    print(f"Decision: {'ACCEPTED' if passed else 'REJECTED'}")
    if rejection_reason:
        print(f"Reason: {rejection_reason}")
    print("="*50 + "\n")

    os.makedirs("reports/evolution", exist_ok=True)
    report_md = engine.create_markdown_report(
        "DonchianBreakoutAgent", baseline_report, hypothesis, hypothesis_report, passed, rejection_reason
    )

    report_path = "reports/evolution/latest.md"
    with open(report_path, "w") as f:
        f.write(report_md)

    logger.info(f"Evolution report saved to {report_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    run_evolution_cycle()
