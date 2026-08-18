
import time
from agents import Agent
from agents import RandomAgent
import random

from domains import NegotiationDomain
import domains



def run_simulation(agents:list[Agent], deadline:float, max_rounds:float):

    """
    args:
        :param NegotiationDomain negotiation_domain: The negotiation domain (i.e. the offer space, the utility functions and the reservation values)
        :param list[Agent] agents:  the two agents that will be negotiating with each other.
        :param float deadline: The maximum time, in seconds, that the negotiations may last.
        :param float max_rounds: The maximum number of rounds that the negotiations may last.
    """

    agreement = None
    current_round = 0
    last_offer = None

    start_time = time.time()
    current_time = 0  # this is the number of seconds that have passed since the start time.

    while(current_time < deadline and current_round < max_rounds):

        # Determine whose turn it is.
        agent_index = current_round % 2
        agent = agents[agent_index]

        # Call the handle_turn method of the agent.
        # Tell the agent the start time, the deadline, and the last offer that was proposed by the other agent.
        # The agent will then return a new proposal, or an acceptance.
        (action_type, offer) = agent.handle_turn(start_time, deadline, last_offer)
        

        # Simulate network latency.
            # In a real negotiation there would be some delay because the proposals are being sent over a network.
            # to simulate network latency, we let the simulation sleep for approximately 10 milliseconds (with 1 millisecond standard deviation).
        delay_ms = random.normalvariate(10,1)
        delay_ms = max(0, delay_ms) # ensure it's non-negative.
        time.sleep(delay_ms / 1000)


        #update the time.
        current_time = time.time() - start_time

        #print(str(current_round+1) + ". " + action_type + " " + str(last_offer))

        # If an agreement was made, then stop the negotiations.
        if(action_type == "accept"):
            agreement = offer
            break

        current_round += 1
        last_offer = offer


    return [agreement, current_round, current_time]




if __name__ == "__main__":

    ## CREATE THE NEGOTIAITION DOMAIN
    negotiation_domain = domains.get_example_domain()


    ## SET THE PARAMETERS OF THE NEGOTIATION
    deadline = 10                   # The deadline in seconds
    max_rounds = float('inf')       # The maximum number of negotiation rounds.  Let's set it to infinity

    ## CREATE TWO AGENTS

    agent0 = RandomAgent(negotiation_domain.offer_space, negotiation_domain.utility_functions[0], negotiation_domain.reservation_values[0], 0)
    agent1 = RandomAgent(negotiation_domain.offer_space, negotiation_domain.utility_functions[1], negotiation_domain.reservation_values[1], 1)

    agents:list[Agent] = [agent0, agent1]

    [agreement, final_round, duration] = run_simulation(agents, deadline, max_rounds)
    
    
    ## Print the results of the negotiation.
    print()
    if(agreement == None):
        print("Negotiations finished without agreement.")
        print("Utility obtained by agent 0: " + str(negotiation_domain.reservation_values[0]))
        print("Utility obtained by agent 1: " + str(negotiation_domain.reservation_values[1]))
    else:
        print("Negotiations finished with agreement, after " + str(final_round) + " proposals and " + str(duration) + " seconds.")
        print("Agreed offer:" + str(agreement))
        print("Utility obtained by agent 0: " + str(negotiation_domain.utility_functions[0].get_utility(agreement)))
        print("Utility obtained by agent 1: " + str(negotiation_domain.utility_functions[1].get_utility(agreement)))

    
