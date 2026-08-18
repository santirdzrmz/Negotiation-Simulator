


from agents import Agent, RandomAgent
from time_based_agent import TimeBasedAgent
from adaptive_agent import AdaptiveAgent
from micro_agent import MiCROAgent
import nego_simulator
import domains
from datetime import datetime

from opponent_utility_models import DummyOpponentUtilityModel
from opponent_strategy_models import SimpleOpponentStrategyModel




def run_tournament():

    ## Create a .csv file to store the results.
    date_string = datetime.today().strftime('%Y-%m-%d %H_%M_%S')
    file_name = date_string + " Negotiation Tournament.csv"
    with open(file_name, 'a') as file:
        file.write("sep=;\n") # This line indicates that we are using the semi-colon as the separator character.
        file.write("Agent 1;Agent 2;Domain;Agreement?;Util 1;Util 2\n")

    # Choose the domains for the tournament:
    all_domains = [domains.get_example_domain(), domains.load_domain_from_folder("Domains/Cinema Date")]

    # Choose the agents for the tournament:
    all_agent_names = ["RandomAgent", "TimeBasedAgent", "AdaptiveAgent", "MiCROAgent"] 

    ## SET THE PARAMETERS OF THE NEGOTIATIONS
    deadline = 10                   # The deadline in seconds
    max_rounds = float('inf')       # The maximum number of negotiation rounds.  Let's set it to infinity

    ## calculate the time required for this tournament:
    num_negotiations = len(all_domains) * len(all_agent_names) * len(all_agent_names)
    tournament_duration_seconds = num_negotiations * deadline
    tournament_duration_minutes = tournament_duration_seconds / 60
    
    print()
    print("This tournament will involve " + str(num_negotiations) + " negotiations, which may take at most " + str(tournament_duration_minutes) + " minutes.")
    print()

    for domain in all_domains:

        for agent_name_0 in all_agent_names:
            for agent_name_1 in all_agent_names:

                ### Intantiate the agents for the next negotiation.
                agent_0 = instantiate_agent(agent_name_0, domain, 0)
                agent_1 = instantiate_agent(agent_name_1, domain, 1)
                agents = [agent_0, agent_1] 

                ### RUN THE NEGOTIATION!
                [agreement, final_round, end_time] = nego_simulator.run_simulation(agents, deadline, max_rounds)


                ### Create a string that summarizes the results of the negotiation
                line = "" + agent_name_0 + ";" + agent_name_1 + ";" + domain.domain_name + ";" 

                if agreement:
                   line += "YES;"
                   line += str(domain.utility_functions[0].get_utility(agreement)) + ";"
                   line += str(domain.utility_functions[1].get_utility(agreement))
                
                else:
                    line += "NO"
                    line += str(domain.reservation_values[0]) + ";"
                    line += str(domain.reservation_values[1])

                ### Print out the results:
                print(line)

                ### Add the results to a .csv file
                with open(file_name, 'a') as file:
                    file.write(line + "\n")


    print("Tournament finished!")

def instantiate_agent(agent_name:str, domain:domains.NegotiationDomain, role_index:int) -> Agent:
    
    util_function = domain.utility_functions[role_index]
    rv = domain.reservation_values[role_index]

    if agent_name == "RandomAgent":
        return RandomAgent(domain.offer_space, util_function, rv, role_index, agent_name)
    
    elif agent_name == "TimeBasedAgent":
        
        opponent_util_function = domain.utility_functions[1-role_index]
        oppModel = DummyOpponentUtilityModel(domain.offer_space, opponent_util_function)

        return TimeBasedAgent(domain.offer_space, util_function, rv, role_index, oppModel, 1, rv, 0.5, agent_name)
    
    elif agent_name == "AdaptiveAgent":

        opponent_util_function = domain.utility_functions[1-role_index]
        opp_util_model = DummyOpponentUtilityModel(domain.offer_space, opponent_util_function)
        
        opp_strategy_model = SimpleOpponentStrategyModel(domain.offer_space, util_function)

        return AdaptiveAgent(domain.offer_space, util_function, rv, role_index, opp_util_model, opp_strategy_model, 1, rv, 0.5, agent_name)
    
    elif agent_name == "MiCROAgent":
        return MiCROAgent(domain.offer_space, util_function, rv, role_index, agent_name)
   
    else:
        raise Exception("Unknown agent: " + agent_name)




if __name__ == "__main__":
    run_tournament()