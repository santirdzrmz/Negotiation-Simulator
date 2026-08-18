

from agents import Agent
from domains import OfferSpace, UtilityFunction
from improved_opponent_models import ImprovedFrequencyAnalysis, RegressionStrategyModel


class VortexAgent(Agent):

    def __init__(
        self,
        offer_space: OfferSpace,
        utility_function: UtilityFunction,
        reservation_value: float,
        agent_index: int,
        concession_param: float = 0.2,
        agent_name: str = "VortexAgent",
    ):
        super().__init__(offer_space, utility_function, reservation_value, agent_index, agent_name)

        self.concession_param = concession_param

        # opponent models
        self.opponent_utility_model  = ImprovedFrequencyAnalysis(offer_space)
        self.opponent_strategy_model = RegressionStrategyModel(offer_space, utility_function)

        # sort all offers by our own utility so we can iterate top-down
        all_offers = offer_space.get_all_offers()
        self.offers_sorted = sorted(all_offers, key=utility_function.get_utility, reverse=True)
        self.max_offer = self.offers_sorted[0]
        self.init_value = utility_function.get_utility(self.max_offer)

        # track what each side has proposed
        self.proposed_by_me:       set = set()
        self.proposed_by_opponent: set = set()

        # utility of each of our proposals over time (time, util)
        self.my_proposal_history:  list[tuple[float, float]] = []

        # floor we never concede below, scaled to how many acceptable offers exist
        n_above_rv = sum(
            1 for o in all_offers
            if utility_function.get_utility(o) > reservation_value
        )
        if n_above_rv < 10:
            self.min_target      = max(reservation_value, 0.50)
            self.panic_threshold = 0.95
        elif n_above_rv < 50:
            self.min_target      = max(reservation_value, 0.45)
            self.panic_threshold = 0.95
        else:
            self.min_target      = max(reservation_value, 0.40)
            self.panic_threshold = 0.95

    def choose_action(self, current_time: float, received_offer):

        # update opponent models with the latest offer
        if received_offer is not None:
            self.opponent_utility_model.update(received_offer, current_time)
            self.opponent_strategy_model.update(received_offer, current_time)
            self.proposed_by_opponent.add(received_offer)

        approx_opp_util = self.opponent_utility_model.get_approximate_utility_function()

        # figure out where we want to land
        target_time  = max(self.deadline * 0.95, current_time)
        target_value = self._compute_target(current_time, target_time)

        # pull back if we are conceding faster than the opponent
        target_value = self._apply_self_mirror(current_time, target_value)

        # current minimum we are willing to accept
        aspiration = self._aspiration(current_time, target_time, target_value)

        # pick the next offer to put on the table
        next_offer = self._select_bid(aspiration, approx_opp_util)

        # decide whether to accept or counter
        accept = self._should_accept(
            received_offer, aspiration, next_offer, current_time, target_value
        )

        if accept:
            return ("accept", received_offer)
        else:
            util_proposed = self.utility_function.get_utility(next_offer)
            self.my_proposal_history.append((current_time, util_proposed))
            self.proposed_by_me.add(next_offer)
            return ("propose", next_offer)


    def _compute_target(self, current_time: float, target_time: float) -> float:
        if current_time == 0:
            return self.init_value

        predicted = self.opponent_strategy_model.predict(current_time, target_time)
        return max(predicted, self.min_target)


    def _apply_self_mirror(self, current_time: float, target_value: float) -> float:
        if current_time < 1.0 or len(self.my_proposal_history) < 2:
            return target_value

        # how fast our utility is dropping per second
        my_start_util = self.my_proposal_history[0][1]
        my_now_util   = self.my_proposal_history[-1][1]
        my_speed = max(0.0, (my_start_util - my_now_util) / current_time)

        # how fast the opponent's offers are improving per second
        opp_data = self.opponent_strategy_model.data_points
        if len(opp_data) < 2:
            return target_value

        opp_start_util = opp_data[0][1]
        opp_now_util   = opp_data[-1][1]
        opp_speed = max(0.0, (opp_now_util - opp_start_util) / current_time)

        # if we are giving in more than twice as fast, nudge the target back up
        if my_speed > 2.0 * opp_speed + 1e-6:
            adjustment = 0.10 * (self.init_value - target_value)
            target_value = min(self.init_value, target_value + adjustment)

        return target_value


    def _aspiration(self, current_time: float, target_time: float, target_value: float) -> float:
        exponent = 1.0 - (current_time / target_time)

        if self.concession_param == 1:
            return (self.init_value - target_value) * exponent + target_value
        else:
            return (
                (self.init_value - target_value)
                * (1 - self.concession_param ** exponent)
                / (1 - self.concession_param)
                + target_value
            )


    def _select_bid(self, aspiration: float, approx_opp_util):
        best_offer = None
        best_score = -1.0
        best_my_util = -1.0

        for offer in self.offers_sorted:
            my_util = self.utility_function.get_utility(offer)

            if my_util < aspiration:
                break  # sorted descending so nothing below this qualifies

            if my_util <= self.reservation_value:
                continue

            if offer in self.proposed_by_me:
                continue

            if approx_opp_util is not None:
                opp_util = approx_opp_util.get_utility(offer)
                score    = my_util * opp_util  # Nash product
            else:
                score = my_util  # no model yet, just use our own utility

            if score > best_score:
                best_score    = score
                best_offer    = offer
                best_my_util  = my_util

        if best_offer is None:
            best_offer   = self.max_offer
            best_my_util = self.init_value

        # if the opponent already proposed something with the same utility for us, reuse it
        TOLERANCE = 1e-9
        for opp_offer in self.proposed_by_opponent:
            opp_my_util = self.utility_function.get_utility(opp_offer)
            if (
                abs(opp_my_util - best_my_util) <= TOLERANCE
                and opp_offer not in self.proposed_by_me
            ):
                best_offer = opp_offer
                break

        return best_offer


    def _should_accept(
        self,
        received_offer,
        aspiration: float,
        next_offer,
        current_time: float,
        target_value: float,
    ) -> bool:

        if received_offer is None:
            return False

        util_received = self.utility_function.get_utility(received_offer)

        if util_received <= self.reservation_value:
            return False

        # take anything above rv when we are almost out of time
        if current_time >= self.panic_threshold * self.deadline:
            return True

        # if the opponent has likely peaked and their offer beats aspiration, take it
        enough_data = len(self.opponent_strategy_model.data_points) >= 5
        past_early  = current_time >= 0.20 * self.deadline
        if enough_data and past_early:
            predicted_best = self.opponent_strategy_model.predict(
                current_time, self.deadline * 0.95
            )
            if util_received >= predicted_best - 1e-6 and util_received >= aspiration:
                return True

        # accept if the offer meets aspiration and is at least as good as our next bid
        util_next = self.utility_function.get_utility(next_offer)
        return util_received >= aspiration and util_received >= util_next
