"""
improved_opponent_models.py
Two improved opponent modeling algorithms used by VortexAgent.

ImprovedFrequencyAnalysis
    Extends the basic frequency analysis with:
    (1) Time-weighted counts — more recent proposals receive a higher weight,
        since the opponent's later offers reveal their true preferences better
        than their opening (typically inflated) proposals.
    (2) Normalised weights — the issue weights are normalised to sum to 1,
        so estimated utility values live on the same [0, 1] scale as our own.
        The basic frequency_analysis.py does not do this, making Nash-product
        comparisons unreliable.

RegressionStrategyModel
    Replaces SimpleOpponentStrategyModel's "highest-received utility, linearly
    extrapolated" approach with an ordinary least-squares regression over ALL
    received offer utilities.  This captures the actual slope of the opponent's
    concession curve and gives a more accurate prediction of where they will
    be at the deadline.
"""

from abc import abstractmethod

from domains import EvaluationFunction, LinearUtilityFunction, OfferSpace, UtilityFunction
from opponent_utility_models import OpponentUtilityModel
from opponent_strategy_models import OpponentStrategyModel

# Improved Frequency Analysis

class ImprovedFrequencyAnalysis(OpponentUtilityModel):
    """
    Frequency-based opponent utility estimator with time-weighting and
    normalised weights.
    """

    def __init__(self, offer_space: OfferSpace):
        self.offer_space = offer_space
        self.num_issues = len(offer_space.issues)
        self.approximate_utility_function = None
        self.proposal_count = 0

        # Weighted frequency table: freq_table[i][o] = cumulative weight for
        # issue i, option o.
        self.freq_table = [
            [0.0] * len(issue.options)
            for issue in offer_space.issues
        ]

    def update(self, received_offer, time: float) -> None:
        """Called every time we receive a new proposal from the opponent."""

        self.proposal_count += 1

        # Recency weight: the k-th proposal gets weight k.
        # This means proposal #10 is 10× more influential than proposal #1,
        # reflecting that later offers are more informative about true preferences.
        weight = float(self.proposal_count)

        # Update weighted counts.
        for i, issue in enumerate(self.offer_space.issues):
            for o, option in enumerate(issue.options):
                if received_offer[i] == option:
                    self.freq_table[i][o] += weight

        # Rebuild the approximate utility function.
        self._rebuild_utility_function()

    def _rebuild_utility_function(self):
        """Recompute the LinearUtilityFunction from the current freq_table."""

        #Evaluation functions (normalised per issue)
        eval_functions = []
        issue_totals = []

        for i, issue in enumerate(self.offer_space.issues):
            total = sum(self.freq_table[i])
            issue_totals.append(total)

            if total == 0:
                # No data yet: uniform distribution.
                evals = [1.0 / len(issue.options)] * len(issue.options)
            else:
                evals = [self.freq_table[i][o] / total for o in range(len(issue.options))]

            eval_functions.append(EvaluationFunction(issue, evals))

        # Issue weights
        # Raw weight for issue i = (max option frequency) / (total weight for issue i).
        # An issue the opponent is very consistent about (always picks the same option)
        # gets a high weight; one they vary freely gets a low weight.
        raw_weights = []
        for i in range(self.num_issues):
            total = issue_totals[i]
            if total == 0:
                raw_weights.append(1.0 / self.num_issues)
            else:
                max_freq = max(self.freq_table[i])
                raw_weights.append(max_freq / total)

        # Normalise so weights sum to 1 — critical for correct Nash product math.
        weight_sum = sum(raw_weights)
        if weight_sum > 0:
            normalised_weights = [w / weight_sum for w in raw_weights]
        else:
            normalised_weights = [1.0 / self.num_issues] * self.num_issues

        self.approximate_utility_function = LinearUtilityFunction(
            normalised_weights, eval_functions
        )

    def get_approximate_utility_function(self) -> LinearUtilityFunction | None:
        return self.approximate_utility_function

# Regression-based Strategy Model

class RegressionStrategyModel(OpponentStrategyModel):
    """
    Predicts the opponent's future concessions using ordinary least-squares
    linear regression over all (time, utility) data points collected so far.

    Compared to SimpleOpponentStrategyModel (which only looks at the single
    highest utility received and extrapolates linearly from the origin), this
    model:
      - Uses ALL data points, not just the maximum.
      - Fits the actual slope and intercept of the opponent's concession curve.
      - Is more robust when the opponent has a non-zero intercept (i.e. they
        don't start at zero utility for us).
    Falls back to the simple max-extrapolation approach when fewer than 3
    proposals have been received (too little data for regression to be reliable).
    """

    def __init__(self, offer_space: OfferSpace, my_utility_function: UtilityFunction):
        self.my_utility_function = my_utility_function

        all_offers = offer_space.get_all_offers()
        utils = [my_utility_function.get_utility(o) for o in all_offers]
        self.max_utility = max(utils)
        self.min_utility = min(utils)

        # Data: list of (time, utility_for_me) tuples.
        self.data_points: list[tuple[float, float]] = []
        self.highest_received = -float('inf')

    def update(self, received_offer, time: float) -> None:
        util = self.my_utility_function.get_utility(received_offer)
        self.data_points.append((time, util))
        self.highest_received = max(self.highest_received, util)

    def predict(self, current_time: float, prediction_time: float) -> float:
        """
        Returns predicted best utility we will receive from the opponent
        at prediction_time.
        """

        if len(self.data_points) < 3:
            # Not enough data: fall back to linear extrapolation from origin.
            if self.highest_received == -float('inf'):
                return self.min_utility
            ratio = prediction_time / max(current_time, 1e-6)
            predicted = self.min_utility + ratio * (self.highest_received - self.min_utility)
            return max(self.min_utility, min(self.max_utility, predicted))

        # Ordinary least-squares: y = a*t + b
        n = len(self.data_points)
        sum_t  = sum(t for t, _ in self.data_points)
        sum_u  = sum(u for _, u in self.data_points)
        sum_tt = sum(t * t for t, _ in self.data_points)
        sum_tu = sum(t * u for t, u in self.data_points)

        denom = n * sum_tt - sum_t ** 2

        if abs(denom) < 1e-10:
            # Degenerate (all proposals at same time): return mean utility.
            return max(self.min_utility, min(self.max_utility, sum_u / n))

        a = (n * sum_tu - sum_t * sum_u) / denom   # slope
        b = (sum_u - a * sum_t) / n                 # intercept

        predicted = a * prediction_time + b
        return max(self.min_utility, min(self.max_utility, predicted))
