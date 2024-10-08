"""
PFlogProfitDrawDownHyperOptLoss

This module defines the alternative HyperOptLoss class based on Profit &
Drawdown & Profit Factor objective which can be used for Hyperoptimization.

Possible to change:
  - `DRAWDOWN_MULT` to penalize drawdown objective for individual needs;
  - `LOG_CONST` to to adjust profit factor impact.
"""

from pandas import DataFrame
import numpy as np

from freqtrade.constants import Config
from freqtrade.data.metrics import calculate_max_drawdown
from freqtrade.optimize.hyperopt import IHyperOptLoss

# smaller numbers penalize drawdowns more severely
DRAWDOWN_MULT = 0.055
# A very large number to use as a replacement for infinity
LARGE_NUMBER = 1e6
# Coefficient to adjust profit factor impact
PF_CONST = 1

class PFlogProfitDrawDownHyperOptLoss(IHyperOptLoss):
    @staticmethod
    def hyperopt_loss_function(results: DataFrame, config: Config, *args, **kwargs) -> float:
        total_profit = results["profit_abs"].sum()

        # Calculate profit factor
        winning_profit = results.loc[results["profit_abs"] > 0, "profit_abs"].sum()
        losing_profit = results.loc[results["profit_abs"] < 0, "profit_abs"].sum()
        profit_factor = winning_profit / abs(losing_profit) if losing_profit else LARGE_NUMBER

        try:
            drawdown = calculate_max_drawdown(
                results, starting_balance=config["dry_run_wallet"], value_col="profit_abs"
            )
            relative_account_drawdown = drawdown.relative_account_drawdown
        except ValueError:
            relative_account_drawdown = 0
        
        # Constant (e.g., 1) to ensure the logarithm is always positive and meaningful
        log_profit_factor = np.log(profit_factor + PF_CONST)
        
        return -1 * (
            (total_profit - (relative_account_drawdown * total_profit) * (1 - DRAWDOWN_MULT)) * log_profit_factor
        )