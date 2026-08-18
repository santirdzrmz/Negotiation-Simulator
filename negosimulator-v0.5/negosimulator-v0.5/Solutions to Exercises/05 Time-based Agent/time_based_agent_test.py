
from agents import Agent
from nego_simulator import run_simulation
from opponent_utility_models import DummyOpponentUtilityModel
from time_based_agent import TimeBasedAgent
from domains import get_example_domain




###############################################################################################################
## NOTE:  TO RUN THIS CODE, YOU MAY FIRST HAVE TO MOVE THIS FILE, AS WELL AS time_based_agent.py UP TO THE MAIN FOLDER CALLED negosimulator.
## OTHERWISE, PYTHON MAY NOT BE ABLE TO RESOLVE THE IMPORTS ABOVE.
###############################################################################################################



if __name__ == "__main__":

    ## CREATE THE NEGOTIAITION DOMAIN
    negotiation_domain = get_example_domain()


    ## SET THE PARAMETERS OF THE NEGOTIATION
    deadline = 10                   # The deadline in seconds
    max_rounds = float('inf')       # The maximum number of negotiation rounds.  Let's set it to infinity




    ## CREATE TWO AGENTS
        # Use the DummyOpponentModel as the opponent modeling algorithm.
        # Note that it uses the utility function of the opponent.

    util0 = negotiation_domain.utility_functions[0]
    util1 = negotiation_domain.utility_functions[1]

    rv0 = negotiation_domain.reservation_values[0]
    rv1 = negotiation_domain.reservation_values[1]


    oppModel0 = DummyOpponentUtilityModel(negotiation_domain.offer_space, util1)
    agent0 = TimeBasedAgent(negotiation_domain.offer_space, util0, rv0, 0, oppModel0, 1, rv0, 1)

    oppModel1 = DummyOpponentUtilityModel(negotiation_domain.offer_space, util0)
    agent1 = TimeBasedAgent(negotiation_domain.offer_space, util1, rv1, 1, oppModel1, 1, rv1, 1)

    agents:list[Agent] = [agent0, agent1]

    run_simulation(negotiation_domain, agents, deadline, max_rounds)



