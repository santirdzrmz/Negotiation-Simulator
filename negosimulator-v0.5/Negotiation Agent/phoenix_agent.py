"""
PhoenixAgent — Custom negotiating agent for the Automated Negotiation assignment.

Design overview
---------------
Bidding strategy:
    Boulware-style time-based aspiration function.  The agent starts near its
    maximum utility and concedes very slowly until roughly 80 % of the
    deadline, then drops more steeply toward the target value.
    Among all offers that are both (a) above the aspiration level and
    (b) above the reservation value, the agent selects the one that
    maximises the Nash product (my_utility × estimated_opponent_utility).
    This steers proposals toward the Pareto frontier rather than just
    maximising own utility.

Opponent modelling:
    FrequencyAnalysis — a real (non-dummy) opponent model that counts how
    often each option appears in the opponent's proposals to estimate their
    weights and evaluation functions.  It requires no knowledge of the
    opponent's true utility function.

Acceptance strategy:
    Three acceptance conditions checked in order:
    1. Panic mode  — if ≥ 95 % of the deadline has elapsed, accept any offer
       strictly above the reservation value (avoid a no-deal).
    2. Normal mode — accept if the received offer's utility is at least as
       high as the aspiration level AND at least as high as the utility of
       the offer we were about to propose.  (Never accept something worse
       than what we were going to counter with.)
    3. Always reject if the received offer's utility is at or below the
       reservation value.
"""

from agents import Agent
from domains import OfferSpace, UtilityFunction
from frequency_analysis import frequencyAnalysis


class PhoenixAgent(Agent):
    """
    Parameters
    ----------
    offer_space          : the negotiation offer space
    utility_function     : our own utility function
    reservation_value    : minimum acceptable utility (walk-away point)
    agent_index          : 0 or 1
    concession_speed     : Boulware exponent β ∈ (0, 1].
                           Lower → more Boulware (stays high longer).
                           Default 0.15 is fairly tough.
    min_target           : floor on the concession target.
                           We never aim lower than max(reservation_value,
                           min_target).  Default 0.3.
    panic_threshold      : fraction of deadline after which panic mode
                           activates.  Default 0.95.
    agent_name           : display name used in tournament output.
    """

    def __init__(
        self,
        offer_space: OfferSpace,
        utility_function: UtilityFunction,
        reservation_value: float,
        agent_index: int,
        concession_speed: float = 0.15,
        min_target: float = 0.3,
        panic_threshold: float = 0.95,
        agent_name: str = "PhoenixAgent",
    ):
        super().__init__(offer_space, utility_function, reservation_value, agent_index, agent_name)

        self.concession_speed = concession_speed
        self.panic_threshold = panic_threshold

        # The agent concedes toward max(rv, min_target) at the deadline.
        self.target_value = max(reservation_value, min_target)

        # Real opponent model: frequency analysis (no peeking at true util).
        self.opponent_model = frequencyAnalysis(offer_space)

        # Pre-sort all offers by own utility descending — used in bidding.
        all_offers = offer_space.get_all_offers()
        self.offers_sorted = sorted(all_offers, key=utility_function.get_utility, reverse=True)

        # Best own offer (used as fallback when aspiration rules out everything).
        self.best_own_offer = self.offers_sorted[0]

        # Track offers already proposed to avoid trivial repetition.
        self.proposed_by_me: set = set()

    # ------------------------------------------------------------------
    # Aspiration function
    # ------------------------------------------------------------------

    def _aspiration(self, t: float) -> float:
        """
        Boulware aspiration function.

        At t=0  → init_value  (= utility of our best offer, ≈ 1.0 normalised)
        At t=T  → target_value

        Formula:  asp(t) = (init − target) × (1 − (t/T)^(1/β)) + target
        where β = concession_speed.

        With small β (e.g. 0.15) the curve stays near init_value for most
        of the deadline and only drops sharply near the end.
        """
        init_value = self.utility_function.get_utility(self.best_own_offer)
        frac = t / self.deadline  # normalised time ∈ [0, 1]
        frac = min(frac, 1.0)

        # Standard Boulware curve: asp = init + (target − init) * frac^(1/β)
        asp = init_value + (self.target_value - init_value) * (frac ** (1.0 / self.concession_speed))
        return asp

    # ------------------------------------------------------------------
    # Main decision method
    # ------------------------------------------------------------------

    def choose_action(self, current_time: float, received_offer):
        """Called by Agent.handle_turn() every round."""

        # ---- 1. Update opponent model ----
        if received_offer is not None:
            self.opponent_model.update(received_offer, current_time)

        approx_opp_util = self.opponent_model.get_approximate_utility_function()

        # ---- 2. Compute aspiration level ----
        asp = self._aspiration(current_time)

        # ---- 3. Select the best offer to propose ----
        next_offer = self._select_bid(asp, approx_opp_util)

        # ---- 4. Decide whether to accept ----
        accept = self._should_accept(received_offer, asp, next_offer, current_time)

        # ---- 5. Return action ----
        if accept:
            return ("accept", received_offer)
        else:
            self.proposed_by_me.add(next_offer)
            return ("propose", next_offer)

    # ------------------------------------------------------------------
    # Bid selection
    # ------------------------------------------------------------------

    def _select_bid(self, aspiration: float, approx_opp_util):
        """
        Among offers that:
          • have not yet been proposed by us, AND
          • yield own utility ≥ aspiration, AND
          • yield own utility > reservation_value

        pick the one that maximises the Nash product (own × opponent).
        If no opponent model is available yet, fall back to max own utility.
        If no offer passes the filter, return the best own offer as fallback.
        """
        best_offer = None
        best_score = -1.0

        for offer in self.offers_sorted:
            my_util = self.utility_function.get_utility(offer)

            # Stop early — list is sorted descending, so nothing below will qualify.
            if my_util < aspiration:
                break

            if my_util <= self.reservation_value:
                continue

            if offer in self.proposed_by_me:
                continue

            if approx_opp_util is not None:
                opp_util = approx_opp_util.get_utility(offer)
                score = my_util * opp_util          # Nash product
            else:
                score = my_util                     # no model yet — be selfish

            if score > best_score:
                best_score = score
                best_offer = offer

        if best_offer is None:
            # Aspiration too high — propose our best offer as a fallback.
            return self.best_own_offer

        return best_offer

    # ------------------------------------------------------------------
    # Acceptance strategy
    # ------------------------------------------------------------------

    def _should_accept(self, received_offer, aspiration: float, next_offer, current_time: float) -> bool:
        if received_offer is None:
            return False

        util_received = self.utility_function.get_utility(received_offer)

        # Never accept at or below reservation value.
        if util_received <= self.reservation_value:
            return False

        # Panic mode: near the deadline, accept anything above RV.
        if current_time >= self.panic_threshold * self.deadline:
            return True

        # Normal mode: accept if at least as good as aspiration AND at
        # least as good as what we were about to propose.
        util_next = self.utility_function.get_utility(next_offer)
        return util_received >= aspiration and util_received >= util_next
