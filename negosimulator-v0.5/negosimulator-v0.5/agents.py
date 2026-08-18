from abc import abstractmethod
import random
import time

from domains import OfferSpace, UtilityFunction


class Agent:


    def __init__(self, offer_space: OfferSpace, utility_function:UtilityFunction, reservation_value:float, agent_index:int, agent_name:str):
        self.offer_space = offer_space
        self.utility_function = utility_function
        self.reservation_value = reservation_value
        self.my_index = agent_index
        self.name = agent_name
        self.opponent_index = 2 - self.my_index
        self.history = []



    def handle_turn(self, start_time:float, deadline:float, received_offer):
        
        """
        args:
            :param float start_time: The time of the start of the negotiations.
            :param float deadline: The total length of the negotiations, in seconds. For example, if deadline==10 it means the negotiations will end 10 seconds after the start of the negotiations.
            :param received_offer: The offer that was last proposed by the other agent. Will be None in the first round.
        """

        current_time = time.time() - start_time
        self.deadline = deadline

        # update the history
        if(received_offer != None):

            #convert the offer received from the opponent into a 'negotiation action' (i.e. adding the index of the agent and the current time.)
            negotiation_action = (self.opponent_index, "propose", received_offer, current_time)
            
            # add it to the history
            self.history.append(negotiation_action)


        
        (action_type, offer) = self.choose_action(current_time, received_offer)


        #convert our own proposal or acceptance into a 'negotiation action' as well.
        current_time = time.time() - start_time
        negotiation_action = (self.my_index, action_type, offer, current_time)
            
        # add it to the history
        self.history.append(negotiation_action)

        return (action_type, offer)

    @abstractmethod
    def choose_action(self, current_time:float, received_offer) -> tuple:
        pass # abstract method.
    




class RandomAgent(Agent):


    def __init__(self, offer_space: OfferSpace, utility_function:UtilityFunction, reservation_value:float, agent_index:int, agent_name="RandomAgent"):
        super().__init__(offer_space, utility_function, reservation_value, agent_index,agent_name)
       
    

    def choose_action(self, current_time:float, received_offer):

        """This method is called from the function handle_turn() in the base class Agent."""

        ## OPPONENT MODELING:
            # The RandomAgent does not use any opponent modeling.



        ## BIDDING STRATEGY:

            # Pick a random offer by selecting, from each issue, a random option.
        random_offer_as_list = []
        for issue in self.offer_space.issues:
            option = random.choice(issue.options)
            random_offer_as_list.append(option)
        
            # convert the list to a tuple.
        next_offer = tuple(random_offer_as_list)



        ## ACCEPTANCE STRATEGY
        if(len(self.history) == 0):
            # If the history is empty (i.e. we have not received any offers yet), then there is nothing to accept.
            accept_offer = False
        else:
            # Otherwise, just randomly choose whether or not to accept the last proposal with a probability of 1%.
            accept_offer = random.randint(1, 100) == 100
        



        ## RETURN SELECTED ACTION
        if(accept_offer):
            return ("accept", received_offer)      
        else:
            return ("propose", next_offer)



def get_last_received_offer(history):

    """ Extracts the last offer from the history.
        Returns 'None' if the history is empty.
    """

    if len(history) == 0:
        return None
   
    # get the last negotiation action from the history.
    last_negotiation_action = history[-1]

    # A negotiation_action is of the form (agent_index, "propose", offer, time)
    # so, to get the last received offer, we have to take the third element from this tuple, i.e. the element with index 2.
    last_received_offer = last_negotiation_action[2]

    return last_received_offer