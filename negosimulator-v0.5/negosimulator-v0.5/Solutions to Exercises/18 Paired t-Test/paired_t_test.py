
import math
from scipy import stats

########################################################################
# NOTE: this file requires downloading and installing the scipy package.  
########################################################################


class NegoResult:

    """Represents the outcome of a single negotiation."""

    def __init__(self, file_row:list[str]):

        self.agent_1 = file_row[0]
        self.agent_2 = file_row[1]
        self.domain_name = file_row[2]

        self.scenario_name = self.domain_name + "_" + self.agent_1 + "_" + self.agent_2

        if file_row[3] == "YES":
            self.agreement = True
        elif file_row[3] == "NO":
            self.agreement = True
        else:
            raise Exception("Error reading file. Unexpected value: " + file_row[3])

        self.util_1 = float(file_row[4])
        self.util_2 = float(file_row[5])

    def get_util(self, agent_index):

        if agent_index == 1:
            return self.util_1
        elif agent_index == 2:
            return self.util_2
        else:
            raise Exception("Illegal index: " + str(agent_index))
        

def get_all_agent_names(nego_results:list[NegoResult]):

    agent_names = set()
    for result in nego_results:
        agent_names.add(result.agent_1)
        agent_names.add(result.agent_2)
    return agent_names

def get_all_domains(nego_results:list[NegoResult]):
    return set([result.domain_name for result in nego_results])

def get_scenario_results(nego_results:list[NegoResult], domain_name, agent_1_name, agent_2_name):
    return [nr for nr in nego_results if nr.domain_name == domain_name and nr.agent_1 == agent_1_name and nr.agent_2 == agent_2_name]

def calculate_scores(scenario_results, agent_index):

    # collect all utility values obtained by the agent with the given index.
    utilities = [nr.get_util(agent_index) for nr in scenario_results]

    # calcualte the average score for this agent in this scenario.
    return average(utilities)

def average(numbers:list[float])-> float:
    return sum(numbers)/len(numbers)

def run_t_test(nego_results:list[NegoResult], high_agent:str, low_agent:str) -> float:

    """ 
    Given the outcomes of all negotiations in a tournament, and the names of two agents (referred to as the 'high agent' and the 'low agent')
    this method calculates the p-value for the alternative hypothesis that the 'high agent' is stronger than the 'low agent'.
    Note that the 'high agent' is assumed to have a higher tournament score than the 'low agent'.
    """

    # Collect the names of all domains in the tournament.
    domains = get_all_domains(nego_results)
    
    # Collect the names of all other agents in the tournament.
    opponents = get_all_agent_names(nego_results)
    opponents.remove(high_agent)
    opponents.remove(low_agent)

    # This list will be used to store the utility differences between the two agents for all domains and opponents.
    data = []

    # 1. Collect data for scenarios in which either the 'high agent' or the 'low agent' was negotiating against some other agent.
    for domain in domains:
        for opponent in opponents:

            # 1a. Collect the results of the two respective agents, for all the negotiations in the given domain, and against the given opponent,
            #  and such that the opponent was playing the role of 'agent 2'.
            high_agent_results = get_scenario_results(nego_results, domain, high_agent, opponent)
            low_agent_results = get_scenario_results(nego_results, domain, low_agent, opponent)
            
            if len(high_agent_results) > 0 and len(low_agent_results) > 0:

                # Calculate the average utility of the 'high agent' in these scenarios.
                av_util_high_agent = calculate_scores(high_agent_results, 1)

                # Calculate the average utility of the 'high agent' in these scenarios.
                av_util_low_agent = calculate_scores(low_agent_results, 1)

                # Calculate the utility difference between the two agents and add it to our data.
                data.append(av_util_high_agent - av_util_low_agent)

            # 1b. Now do the same again, but this time for those scenarios in which the opponent was playing the role of 'agent 1'.
            high_agent_results = get_scenario_results(nego_results, domain, opponent, high_agent)
            low_agent_results = get_scenario_results(nego_results, domain, opponent, low_agent)

            if len(high_agent_results) > 0 and len(low_agent_results) > 0:

                av_util_high_agent = calculate_scores(high_agent_results, 2)
                av_util_low_agent = calculate_scores(low_agent_results, 2)
                data.append(av_util_high_agent - av_util_low_agent)


    # 2. Collect data for scenarios in which the two given agents were negotiating against each other.
    for domain in domains:
       
        results_high_vs_low = get_scenario_results(nego_results, domain, high_agent, low_agent)
        av_util_high_agent = calculate_scores(results_high_vs_low, 1) # av. utility of the 'high agent' against the 'low agent'.
        av_util_low_agent = calculate_scores(results_high_vs_low, 2)  # av. utility of the 'low agent' against the 'high agent'.
        data.append(av_util_high_agent - av_util_low_agent)

        results_low_vs_high = get_scenario_results(nego_results, domain, low_agent, high_agent)
        av_util_high_agent = calculate_scores(results_low_vs_high, 2)
        av_util_low_agent = calculate_scores(results_low_vs_high, 1)
        data.append(av_util_high_agent - av_util_low_agent)




    # 3. Collect data for the 'self-play scenarios', i.e. the scenarios in which either the 'high agent' or the 'low agent' was negotiating against itself.
    
    # these data will be stored in the same list as the other data, but on top of that they will also be stored in the following two separate lists,
    # which will be useful to calculate the 'covariance terms', which only involve results from the self-play scenarios.
    self_play_data_1 = []
    self_play_data_2 = []

    for domain in domains:
        results_high_vs_high = get_scenario_results(nego_results, domain, high_agent, high_agent)
        results_low_vs_low = get_scenario_results(nego_results, domain, low_agent, low_agent)

        av_util_high_agent = calculate_scores(results_high_vs_high, 1)
        av_util_low_agent = calculate_scores(results_low_vs_low, 1)
        data.append(av_util_high_agent - av_util_low_agent)
        self_play_data_1.append(av_util_high_agent - av_util_low_agent)

        av_util_high_agent = calculate_scores(results_high_vs_high, 2)
        av_util_low_agent = calculate_scores(results_low_vs_low, 2)
        data.append(av_util_high_agent - av_util_low_agent)
        self_play_data_2.append(av_util_high_agent - av_util_low_agent)

    
    # 4. Use the collected data to calculate the standard error of the utility difference between the two agents. 

    #    4a. Calculate the mean of the data.
    av = average(data)

    # The 'high agent' should, by definition, be the agent with the higher tournament score, 
    # and therefore the average of the utility differences between the two agents should be positive. 
    if av < 0:
        raise Exception("The tournament score of the 'high agent' should be greater than the tournament score of the 'low agent', but the opposite seems to be true.")



    num_domains = len(domains)
    num_agents = len(opponents)+2
    k = 2*num_domains*num_agents

    sum_of_square_diffs = sum((x-av)*(x-av) for x in data)
    
    sum_of_covariance_terms = sum((av-self_play_data_1[d])*(av-self_play_data_2[d]) for d in range(num_domains))

    variance = (sum_of_square_diffs + 2*sum_of_covariance_terms) / (k*(k-1))
    standard_error = math.sqrt(variance)

    # 5. Use this to calculate the t-statistic and the p-value.
    t_statistic = av / standard_error

    p_value = 1 - stats.t.cdf (t_statistic, k-1)

    return float(p_value)



