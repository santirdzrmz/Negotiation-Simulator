# Negotiation Simulator

A framework and coursework project for building and evaluating **autonomous bilateral negotiation agents**. Two agents negotiate over a multi-issue "offer space" (e.g. which car brand and color to buy) under a time deadline, each trying to maximize its own private utility function while the other agent does the same. The project implements several agent strategies, opponent-modeling algorithms, and a tournament system to compare them head-to-head.

## Core framework

- **`domains.py`** — Defines the negotiation problem: an `Issue` (e.g. "Brand" with options `Volvo`/`Ford`/`Ferrari`), an `OfferSpace` (the cartesian product of all issues), an `EvaluationFunction` (how much each option is worth to an agent), a `LinearUtilityFunction` (weighted sum of evaluations across issues), and a `NegotiationDomain` that ties an offer space, both agents' utility functions, and their reservation values together. Domains can be hand-built (`get_example_domain`) or loaded from paired JSON files (`load_domain_from_folder`, see `Domains/Cinema Date/`).
- **`agents.py`** — Defines the abstract `Agent` base class. Each turn, `handle_turn()` records the offer it just received, calls the subclass's `choose_action()` to decide whether to `propose` a new offer or `accept` the last one, and logs the action to `self.history`. `RandomAgent` is the simplest baseline: it proposes random offers and accepts with a small fixed probability.
- **`nego_simulator.py`** — Runs a single negotiation between two agents (`run_simulation`), alternating turns until one side accepts, the round limit is hit, or the time deadline passes. Returns the agreed offer (or `None`) plus the round count and duration.

## Agent strategies implemented

| Agent | Bidding strategy | Opponent modeling | Notes |
|---|---|---|---|
| `RandomAgent` | Random offer each turn | None | Baseline |
| `TimeBasedAgent` | Time-dependent concession curve (Boulware / Linear / Conceder, via `concession_param`) | `DummyOpponentUtilityModel` (baseline that "cheats" by perturbing the true opponent utility) | `time_based_agent.py` |
| `AdaptiveAgent` | Concedes based on a modeled prediction of how far the opponent will concede | `SimpleOpponentStrategyModel` (linear extrapolation of the opponent's best offer so far) | `adaptive_agent.py` |
| `MiCROAgent` | Concedes to the next-best offer only once the opponent has proposed at least as many unique offers as we have | None | `micro_agent.py` |
| `PhoenixAgent` | Boulware-style aspiration curve; among acceptable offers, picks the one maximizing the Nash product (own utility × estimated opponent utility) to aim for Pareto-efficient deals; panics and accepts anything above reservation value near the deadline | `frequencyAnalysis` — estimates the opponent's utility function from how often they propose each option | `phoenix_agent.py`, `frequency_analysis.py` |
| `VortexAgent` | Similar Boulware/Nash-product approach with a utility floor that scales with domain size | `ImprovedFrequencyAnalysis` (time-weighted, normalized frequency counts) + `RegressionStrategyModel` (least-squares fit of the opponent's concession curve) | `vortex_agent.py`, `improved_opponent_models.py` |

`PhoenixAgent` and `VortexAgent` are the custom agents built for this project; the others are framework/course-exercise implementations they build on and compete against.

## Domain generation

`domain_generator.py` procedurally generates randomized negotiation domains of varying size (2–5 issues, 2–4 options each) and competitiveness (cooperative domains where a (1,1)-utility deal exists, vs. more zero-sum competitive domains), used to stress-test agents beyond the fixed example/Cinema Date domains.

## Tournament and analysis

- **`tournament.py`** — Runs a full round-robin tournament: every agent plays every agent (including itself) across every domain (the example domain, the Cinema Date domain, and the generated domains), repeated several times for statistical stability. Results are written to a timestamped CSV (`Agent1;Agent2;Domain;Agreement;Util1;Util2`).
- **`analyze_tournament.py`** — Reads a tournament results CSV and reports each agent's average score, standard error, utility-on-agreement, and agreement rate; builds a payoff matrix and flags symmetric Nash equilibria; and breaks results down by domain type (size × competitiveness).

## Repository layout

```
README.md
negosimulator-v0.5/
├── negosimulator-v0.5/            # Base framework as provided for the course
│   ├── agents.py, domains.py, nego_simulator.py, ...
│   ├── Domains/Cinema Date/        # Example JSON-defined negotiation domain
│   └── Solutions to Exercises/     # Step-by-step course exercises (domain
│                                    # generator, visualizer, time-based agent,
│                                    # adaptive agent, MiCRO agent, tournament
│                                    # running/scoring, statistical tests, etc.)
└── Negotiation Agent/              # Final project workspace
    ├── phoenix_agent.py, vortex_agent.py, improved_opponent_models.py, ...
    ├── tournament.py, analyze_tournament.py, domain_generator.py
    ├── *.csv                       # Saved tournament results
    └── Negotiation_Report.docx     # Write-up of the approach and results
```

## Running a tournament

From inside `negosimulator-v0.5/Negotiation Agent/`:

```bash
python tournament.py               # Runs the round-robin tournament, saves a timestamped CSV
python analyze_tournament.py <csv> # Prints scores, Nash equilibria, and domain-type breakdowns
```

## Status

This is a course project (bilateral automated negotiation, ANAC/ANL-style). The base `negosimulator-v0.5/negosimulator-v0.5` folder holds the unmodified course framework and exercise solutions; the actively developed agents, tournament results, and write-up live under `negosimulator-v0.5/Negotiation Agent/`.
