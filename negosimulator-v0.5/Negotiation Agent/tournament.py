"""
tournament.py
-------------
Runs a round-robin tournament between all agent variants.
Results are saved to a timestamped CSV file.

Usage (from the Negotiation Agent/ folder):
    python tournament.py

The CSV can then be analysed with analyze_tournament.py.
"""

import nego_simulator
import domains as domain_module
from datetime import datetime

from agents import Agent, RandomAgent
from time_based_agent import TimeBasedAgent
from adaptive_agent import AdaptiveAgent
from micro_agent import MiCROAgent
from phoenix_agent import PhoenixAgent
from vortex_agent import VortexAgent

from opponent_utility_models import DummyOpponentUtilityModel
from opponent_strategy_models import SimpleOpponentStrategyModel
from frequency_analysis import frequencyAnalysis

from domain_generator import generate_domains


# ---------------------------------------------------------------------------
# Agent instantiation
# ---------------------------------------------------------------------------

def instantiate_agent(agent_name: str, domain: domain_module.NegotiationDomain, role_index: int) -> Agent:

    util_fn  = domain.utility_functions[role_index]
    opp_util = domain.utility_functions[1 - role_index]
    rv       = domain.reservation_values[role_index]
    offer_sp = domain.offer_space

    if agent_name == "RandomAgent":
        return RandomAgent(offer_sp, util_fn, rv, role_index, agent_name)

    elif agent_name == "TimeBased_Boulware":
        opp_model = DummyOpponentUtilityModel(offer_sp, opp_util)
        return TimeBasedAgent(offer_sp, util_fn, rv, role_index, opp_model,
                              init_value=1.0, target_value=rv, concession_param=0.1,
                              agent_name=agent_name)

    elif agent_name == "TimeBased_Linear":
        opp_model = DummyOpponentUtilityModel(offer_sp, opp_util)
        return TimeBasedAgent(offer_sp, util_fn, rv, role_index, opp_model,
                              init_value=1.0, target_value=rv, concession_param=1.0,
                              agent_name=agent_name)

    elif agent_name == "TimeBased_Conceder":
        opp_model = DummyOpponentUtilityModel(offer_sp, opp_util)
        return TimeBasedAgent(offer_sp, util_fn, rv, role_index, opp_model,
                              init_value=1.0, target_value=rv, concession_param=5.0,
                              agent_name=agent_name)

    elif agent_name == "AdaptiveAgent":
        opp_util_model     = DummyOpponentUtilityModel(offer_sp, opp_util)
        opp_strategy_model = SimpleOpponentStrategyModel(offer_sp, util_fn)
        return AdaptiveAgent(offer_sp, util_fn, rv, role_index,
                             opp_util_model, opp_strategy_model,
                             init_value=1.0, minimum_target_value=rv,
                             concession_param=0.5,
                             agent_name=agent_name)

    elif agent_name == "MiCROAgent":
        return MiCROAgent(offer_sp, util_fn, rv, role_index, agent_name)

    elif agent_name == "PhoenixAgent":
        return PhoenixAgent(offer_sp, util_fn, rv, role_index,
                            concession_speed=0.15, min_target=0.3,
                            panic_threshold=0.95,
                            agent_name=agent_name)

    elif agent_name == "VortexAgent":
        return VortexAgent(offer_sp, util_fn, rv, role_index,
                           concession_param=0.2,
                           agent_name=agent_name)

    else:
        raise ValueError(f"Unknown agent name: {agent_name}")


# ---------------------------------------------------------------------------
# Tournament runner
# ---------------------------------------------------------------------------

def run_tournament(num_repetitions: int = 5):
    """
    Run a full round-robin tournament.

    num_repetitions: how many times each (agent_A, agent_B, domain) triple
                     is repeated.  More repetitions → lower standard error.
    """

    # Agents to include in the tournament
    all_agent_names = [
        "RandomAgent",
        "TimeBased_Boulware",
        "TimeBased_Conceder",
        "AdaptiveAgent",
        "MiCROAgent",
        "PhoenixAgent",
        "VortexAgent",
    ]

    # Domains: built-in example + Cinema Date + random generated domains
    all_domains = []
    all_domains.append(domain_module.get_example_domain())
    all_domains.append(domain_module.load_domain_from_folder("Domains/Cinema Date"))
    all_domains.extend(generate_domains())

    deadline   = 10           # seconds per negotiation (matches final tournament)
    max_rounds = float('inf')

    # Calculate and display expected runtime
    num_negotiations = (len(all_agent_names) ** 2) * len(all_domains) * num_repetitions
    est_minutes = num_negotiations * deadline / 60
    print(f"\nTournament: {len(all_agent_names)} agents × {len(all_domains)} domains × "
          f"{num_repetitions} reps = {num_negotiations} negotiations")
    print(f"Estimated max duration: {est_minutes:.1f} minutes\n")

    # Open CSV output file
    date_str  = datetime.today().strftime('%Y-%m-%d %H_%M_%S')
    file_name = f"{date_str} Tournament Results.csv"

    with open(file_name, 'w') as f:
        f.write("sep=;\n")
        f.write("Agent1;Agent2;Domain;Agreement;Util1;Util2\n")

    completed = 0
    for domain in all_domains:
        for name_0 in all_agent_names:
            for name_1 in all_agent_names:
                for _ in range(num_repetitions):

                    agent_0 = instantiate_agent(name_0, domain, 0)
                    agent_1 = instantiate_agent(name_1, domain, 1)

                    [agreement, final_round, duration] = nego_simulator.run_simulation(
                        [agent_0, agent_1], deadline, max_rounds
                    )

                    if agreement is not None:
                        u0 = domain.utility_functions[0].get_utility(agreement)
                        u1 = domain.utility_functions[1].get_utility(agreement)
                        line = f"{name_0};{name_1};{domain.domain_name};YES;{u0:.4f};{u1:.4f}"
                    else:
                        rv0 = domain.reservation_values[0]
                        rv1 = domain.reservation_values[1]
                        line = f"{name_0};{name_1};{domain.domain_name};NO;{rv0:.4f};{rv1:.4f}"

                    completed += 1
                    if completed % 50 == 0:
                        print(f"  {completed}/{num_negotiations} negotiations done …")

                    with open(file_name, 'a') as f:
                        f.write(line + "\n")

    print(f"\nTournament finished! Results saved to: {file_name}")
    return file_name


if __name__ == "__main__":
    run_tournament(num_repetitions=3)
