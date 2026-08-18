
import csv



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

        return av_util


def average(numbers:list[float])-> float:
    return sum(numbers)/len(numbers)
            
if __name__ == '__main__':
    
    # 1. Parse the results from the individual negotiations from the file
    nego_results = parse_file("test.csv")

    # 2. Obtain the names of all domains used in the tournament. 
    domains = get_all_domains(nego_results)

    # 3. Obtain the names of all agents involved in the tournament.
    agents = get_all_agent_names(nego_results)

    # 4a. loop over all scenarios that involved this agent, and for each such scenario,
    #       calculate the agent's average score over all negotiations in that scenario.
    for agent in agents:

        av_util_per_scenario = []

        # loop over all scenarios that involved this agent, and for each such scenario, 
        # calculate the agent's average score over all negotiations in that scenario.
        for domain in domains:
            for opponent in agents:

                # Collect the results of all the negotiations in the scenario (domain, agent, opponent)
                scenario_results = get_scenario_results(nego_results, domain, agent, opponent)

                if len(scenario_results) > 0:
                
                    av_util = calculate_scores(scenario_results, 1)

                    av_util_per_scenario.append(av_util)

                # Next, do the same but now for the scenario in which this agent played the role of agent 2:

                scenario_results = get_scenario_results(nego_results, domain, opponent, agent)

                if len(scenario_results) > 0:
                
                    av_util = calculate_scores(scenario_results, 2)

                    av_util_per_scenario.append(av_util)


        # Now calculate the average over all scenarios.
        tournament_score = average(av_util_per_scenario)

        

        # TODO: make sure that the agents are printed in order of decreasing tournament score.
        
        print(agent + " " + str(tournament_score))

    