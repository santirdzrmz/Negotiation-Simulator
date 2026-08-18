

import random
from agents import Agent
from domains import OfferSpace, UtilityFunction



class MiCROAgent(Agent):

    def __init__(self, offer_space: OfferSpace, utility_function:UtilityFunction, reservation_value:float, agent_index:int, agent_name:str):
        super().__init__(offer_space, utility_function, reservation_value, agent_index, agent_name)


        self.num_proposed_by_me = 0

        # We use this set to store the offers that we have already received.
        self.proposed_by_opponent:set = set()

        # Create a list of offers, sorted in order of decreasing utility.
        offers = offer_space.get_all_offers()
        self.offers_sorted = sorted(offers, key=utility_function.get_utility, reverse=True)


    def choose_action(self, current_time:float, received_offer):

        """ This method is called from the function handle_turn() in the base class Agent. """

        ## OPPONENT MODELING:
            # MiCRO doesn't apply any opponent modeling!


        ## BIDDING STRATEGY:

            # Count how many unique proposals have so far been made by the opponent.
        self.proposed_by_opponent.add(received_offer)
        num_proposed_by_opponent = len(self.proposed_by_opponent)

            # Determine which offer we would propose next, if we are ready to concede.
        next_offer = self.offers_sorted[self.num_proposed_by_me]
        util_of_next_offer = self.utility_function.get_utility(next_offer)

            # Determine whether or not we should make a concession in this round.
        ready_to_concede = (self.num_proposed_by_me <= num_proposed_by_opponent) and (util_of_next_offer > self.reservation_value)

            
        if ready_to_concede:
            # We will be proposing a new offer (one we haven't proposed before), so we can increase this number. 
            self.num_proposed_by_me += 1
            
            # Note: it may actually happen that we will *accept* the received offer, rather than proposing a new offer, but in that case the negotiations will be finished anyway,
            # so it no longer matters that this number is not updated correctly.
        
        else:
            # If we are not conceding, then randomly choose an offer that we have already proposed earlier.
            r = random.randint(0,self.num_proposed_by_me-1)
            next_offer = self.offers_sorted[r]
            



        ## ACCEPTANCE STRATEGY:
        if received_offer == None:
            accept_offer = False
        else:

            # Determine our 'acceptance threshold' (i.e. the utility we are willing to accept.)
            if ready_to_concede:
                acceptance_threshold = util_of_next_offer
                
            else:
                lowest_proposed_offer = self.offers_sorted[self.num_proposed_by_me-1]
                acceptance_threshold = self.utility_function.get_utility(lowest_proposed_offer)

            util_of_received_offer = self.utility_function.get_utility(received_offer)
            accept_offer = (acceptance_threshold <= util_of_received_offer)




        ## Return our decision: accept the received offer, or propose a new offer.
        if accept_offer:
            return ("accept", received_offer)
        else:
            return ("propose", next_offer)
