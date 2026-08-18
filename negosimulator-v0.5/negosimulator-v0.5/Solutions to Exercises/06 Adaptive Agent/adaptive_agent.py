

from agents import Agent
from domains import UtilityFunction, OfferSpace
from opponent_strategy_models import OpponentStrategyModel
from opponent_utility_models import OpponentUtilityModel




class AdaptiveAgent(Agent):

    def __init__(self, offer_space: OfferSpace, utility_function:UtilityFunction, reservation_value:float, agent_index:int, opponent_utility_model:OpponentUtilityModel, opponent_strategy_model:OpponentStrategyModel, init_value:float, minimum_target_value:float, concession_param:float, agent_name="AdaptiveAgent"):
        super().__init__(offer_space, utility_function, reservation_value, agent_index, agent_name)


        # The opponent modeling algorithm that we will use to estimate the opponent's utility funcion.
        self.opponent_utility_model:OpponentUtilityModel = opponent_utility_model

        # The opponent modeling algorithm that we will use to estimate the opponent's future proposals.
        self.opponent_strategy_model:OpponentStrategyModel = opponent_strategy_model

        # The parameters that determine the aspiration function.
        self.init_value:float = init_value
        self.minimum_target_value:float = minimum_target_value
        self.concession_param:float = concession_param

        # We use this set to store the offers that we have already proposed. This is to ensure that we don't repeat offers.
        self.proposed_by_me:set = set()


        # Determine the offer that gives us the highest utility.
        # We will propose that offer in case there is no offer that satisfies our normal criteria.
        self.max_offer = None
        highest_util = 0
        for offer in self.offer_space.get_all_offers():
            
            util = self.utility_function.get_utility(offer)

            if self.max_offer == None or util > highest_util:
                self.max_offer = offer
                highest_util = util



    def choose_action(self, current_time:float, received_offer):

        """This method is called from the function handle_turn() in the base class Agent."""



        ## OPPONENT MODELING:
        if received_offer != None:
            self.opponent_utility_model.update(received_offer, current_time)
            self.opponent_strategy_model.update(received_offer, current_time)
        
        approximate_opponent_utility = self.opponent_utility_model.get_approximate_utility_function()
        


        # use the opponent strategy model to determine our target value.
        target_time = max(self.deadline*0.95, current_time)
        
        if current_time == 0:
            target_value = self.utility_function.get_utility(self.max_offer)
        else:
            
            target_value = self.opponent_strategy_model.predict(current_time, target_time)
            #print("target_value: " + str(target_value))
            
            # Make sure that the target value does not get lower than the minimum target value.
            target_value =  max(target_value, self.minimum_target_value)
            

        ## BIDDING STRATEGY:

            ## 1. Calculate our aspiration level.
        exponent = 1 - (current_time / target_time)
        if(self.concession_param == 1):
            # In the special case that self.concession_param == 1 the standard calculation, below, would yield a division-by-zero error.
            aspiration_level = (self.init_value - target_value) * (exponent)  + target_value
        else:
            aspiration_level = (self.init_value - target_value) * (1-pow(self.concession_param, exponent))/(1-self.concession_param)  + target_value

            ## 2. Determine our next offer to propose: 
            #  Among all offers that haven't yet been proposed by me, and 
            #  for which my utility is at least as high as my aspiration level,
            #  find the offer with highest opponent utility (according to our opponent model).

        next_offer = None
        max_opp_util = 0
        for offer in self.offer_space.get_all_offers():
            
            if offer in self.proposed_by_me:
                continue

            my_util = self.utility_function.get_utility(offer)
            if my_util < aspiration_level:
                continue

            if approximate_opponent_utility == None:
                break

            opp_util = approximate_opponent_utility.get_utility(offer)
            if opp_util > max_opp_util:
                max_opp_util = opp_util
                next_offer = offer


        ## If no such offer exists, propose the one that yields highest utility to us.
        ## TODO Implement a better solution: propose a random offer that is higher than our aspiration level.
        if next_offer == None:
            next_offer = self.max_offer

        

        ## ACCEPTANCE STRATEGY:
        if received_offer == None:
            accept_offer = False
        else:
            #print("my asp level: " + str(aspiration_level) + " my util of received offer: " + str(self.utility_function.get_utility(received_offer)) + " my util of proposed offer: " + str(self.utility_function.get_utility(next_offer)))
            util_received_offer = self.utility_function.get_utility(received_offer)
            accept_offer = (util_received_offer >= aspiration_level and util_received_offer > self.reservation_value)


        ## Return our decision: accept the received offer, or propose a new offer.
        if accept_offer:
            return ("accept", received_offer)
        else:
            self.proposed_by_me.add(next_offer)
            return ("propose", next_offer)
