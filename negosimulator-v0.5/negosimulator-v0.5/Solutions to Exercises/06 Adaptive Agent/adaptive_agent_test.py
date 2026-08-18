
from agents import Agent
from nego_simulator import run_simulation
from adaptive_agent import AdaptiveAgent
from domains import get_example_domain
from opponent_strategy_models import SimpleOpponentStrategyModel
from opponent_utility_models import DummyOpponentUtilityModel




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

    agent_index_0 = 0
    oppUtilModel0 = DummyOpponentUtilityModel(negotiation_domain.offer_space, util1)
    oppStratModel0 = SimpleOpponentStrategyModel(negotiation_domain.offer_space, util0)
    agent0 = AdaptiveAgent(negotiation_domain.offer_space, util0, rv0, agent_index_0, oppUtilModel0, oppStratModel0, init_value=1, minimum_target_value=rv0, concession_param=1)
    #TO DO: choose a better 'minimum target value'.

    agent_index_1 = 1
    oppUtilModel1 = DummyOpponentUtilityModel(negotiation_domain.offer_space, util0)
    oppStratModel1 = SimpleOpponentStrategyModel(negotiation_domain.offer_space, util1)
    agent1 = AdaptiveAgent(negotiation_domain.offer_space, util1, rv1, agent_index_1, oppUtilModel1, oppStratModel1, init_value=1, minimum_target_value=rv1, concession_param=1)
    #TO DO: choose a better 'minimum target value'.

    
    agents:list[Agent] = [agent0, agent1]

    run_simulation(negotiation_domain, agents, deadline, max_rounds)



