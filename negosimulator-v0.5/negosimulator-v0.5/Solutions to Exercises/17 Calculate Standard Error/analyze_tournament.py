import csv
import math



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


def parse_file(file_name) -> list[NegoResult]:

    results = []

    with open(file_name, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')

        row_counter = 0

        for row in reader:

            row_counter += 1
            if row_counter <= 2:
                continue

            result = NegoResult(row)

            results.append(result)

    return results


def get_all_agent_names(nego_results:list[NegoResult]):

    agent_names = set()
    for result in nego_results:
        agent_names.add(result.agent_1)
        agent_names.add(result.agent_2)
    return agent_names

def get_all_domains(nego_results:list[NegoResult]):
    return set([result.domain_name for result in nego_results])

def get_all_scenarios(nego_results:list[NegoResult]):
    return set([result.scenario_name for result in nego_results])


def get_scenario_results(nego_results:list[NegoResult], domain_name, agent_1_name, agent_2_name):
    return [nr for nr in nego_results if nr.domain_name == domain_name and nr.agent_1 == agent_1_name and nr.agent_2 == agent_2_name]


def calculate_scores(scenario_results, agent_index):

        # collect all utility values obtained by the agent with the given index.
        utilities = [nr.get_util(agent_index) for nr in scenario_results]

        # calcualte the average score for this agent in this scenario.
        av_util = average(utilities)

        utilities_on_agreement = [nr.get_util(agent_index) for nr in scenario_results if nr.agreement]
        av_util_on_agreement = average(utilities_on_agreement) # TODO: this will raise an exception if no agreement was made in this scenario.

        # calculuate the agreement rate for this agent in this scnenario, and add it to the list.
        agreement_rate = sum(1 for nr in scenario_results if nr.agreement) / len(scenario_results)


        return [av_util, av_util_on_agreement, agreement_rate]


def average(numbers:list[float])-> float:
    return sum(numbers)/len(numbers)

if __name__ == '__main__':

    # 1. Parse the results from the individual negotiations from the file
    nego_results = parse_file("test.csv")

    # 2. Obtain the names of all domains used in the tournament.
    domains = get_all_domains(nego_results)

    # 3. Obtain the names of all agents involved in the tournament.
    agents = get_all_agent_names(nego_results)

    # 4. Calcluate the scores of each agent:
    for agent in agents:

        av_util_per_scenario = []
        av_util_on_agreement_per_scenario = []
        agreement_rate_per_scenario = []

        # For each self-play scenario, stores the average utility of agent 1
        av_util_1_self_play_scenarios = []

        # For each self-play scenario, stores the average utility of agent 2
        av_util_2_self_play_scenarios = []

        # 4a. loop over all scenarios that involved this agent, and for each such scenario,
        #       calculate the agent's average score over all negotiations in that scenario.
        for domain in domains:
            for opponent in agents:

                # Collect the results of all the negotiations in the scenario (domain, agent, opponent)
                scenario_results = get_scenario_results(nego_results, domain, agent, opponent)

                if len(scenario_results) > 0:

                    [av_util, av_util_on_agreement, agreement_rate] = calculate_scores(scenario_results, 1)

                    av_util_per_scenario.append(av_util)
                    av_util_on_agreement_per_scenario.append(av_util_on_agreement)
                    agreement_rate_per_scenario.append(agreement_rate)

                    if agent == opponent:
                        av_util_1_self_play_scenarios.append(av_util)

                # Next, do the same but now for the scenario in which this agent played the role of agent 2:

                scenario_results = get_scenario_results(nego_results, domain, opponent, agent)

                if len(scenario_results) > 0:

                    [av_util, av_util_on_agreement, agreement_rate] = calculate_scores(scenario_results, 2)

                    av_util_per_scenario.append(av_util)
                    av_util_on_agreement_per_scenario.append(av_util_on_agreement)
                    agreement_rate_per_scenario.append(agreement_rate)

                    if agent == opponent:
                        av_util_2_self_play_scenarios.append(av_util)

        # 4b. Now calculate the averages over all scenarios.
        tournament_score = average(av_util_per_scenario)
        av_util_on_agreement = average(av_util_on_agreement_per_scenario)
        av_agreement_rate = average(agreement_rate_per_scenario)

        # 4c. Calculate the standard error
        
        #   4c_1 For each scenario s, calcuate the difference mu_{tot} - mu_{s}
        diffs = [(tournament_score - mean) for mean in av_util_per_scenario]
        
        #   4c_2 Calculate the sum of the squares of those differences
        sum_of_squares = sum(diff * diff for diff in diffs) 
        
        #   4c_3. Add covariance terms for the self-play scenarios.
        for d in range(len(domains)):
            sum_of_squares += 2*(tournament_score - av_util_1_self_play_scenarios[d])*(tournament_score - av_util_2_self_play_scenarios[d])

        #   4c_4. Divide by k*(k-1) and take the square root.
        k = 2 * len(agents) * len(domains)
        std_err_squared = sum_of_squares / (k * (k-1))
        std_err = math.sqrt(std_err_squared)


        # TODO: make sure that the agents are printed in order of decreasing tournament score.

        print(agent + " " + str(tournament_score) + " +/- " + str(std_err) + " " + str(av_util_on_agreement) + " " + str(100 * av_agreement_rate) + "%")