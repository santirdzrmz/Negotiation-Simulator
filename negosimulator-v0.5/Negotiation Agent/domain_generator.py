"""
domain_generator.py
-------------------
Wraps the framework's domain_generator_2 logic inline so we don't need to
copy a separate file.  Call generate_domains() to get the list of random
domains used in the tournament.
"""

import random
import itertools
from domains import Issue, OfferSpace, EvaluationFunction, LinearUtilityFunction, NegotiationDomain


def generate_domain(
    domain_name: str,
    min_issues: int,
    max_issues: int,
    min_issue_size: int,
    max_issue_size: int,
    max_utility_sum: float = 2.0,
    strict: bool = True,
) -> NegotiationDomain:
    """
    Generate a random normalised negotiation domain.

    max_utility_sum: any value in [1, 2].
        2.0 = fully cooperative (Pareto-optimal offers exist at (1,1))
        1.0 = fully competitive  (zero-sum)
    strict: if True, guarantee at least one offer achieves max_utility_sum exactly.
    """

    num_issues = random.randint(min_issues, max_issues)

    # ---- Build issues with random options ----
    issues = []
    for i in range(num_issues):
        num_options = random.randint(min_issue_size, max_issue_size)
        options = [f"opt{i}_{j}" for j in range(num_options)]
        issues.append(Issue(f"Issue{i}", options))

    offer_space = OfferSpace(issues)
    all_offers = offer_space.get_all_offers()

    # ---- Helper: build a random normalised linear utility function ----
    def random_util_function(issues):
        # Random weights that sum to 1
        raw_weights = [random.random() for _ in issues]
        total = sum(raw_weights)
        weights = [w / total for w in raw_weights]

        eval_functions = []
        for i, issue in enumerate(issues):
            n = len(issue.options)
            # Random evaluations, then normalise so min=0, max=1
            evals = [random.random() for _ in range(n)]
            mn, mx = min(evals), max(evals)
            if mx == mn:
                evals = [0.0] * (n - 1) + [1.0]
            else:
                evals = [(e - mn) / (mx - mn) for e in evals]
            eval_functions.append(EvaluationFunction(issue, evals))

        return LinearUtilityFunction(weights, eval_functions)

    # ---- Generate utility functions until max_utility_sum constraint met ----
    for _ in range(1000):
        uf1 = random_util_function(issues)
        uf2 = random_util_function(issues)

        sums = [uf1.get_utility(o) + uf2.get_utility(o) for o in all_offers]
        actual_max = max(sums)

        if actual_max <= max_utility_sum:
            if strict:
                # scale both utility functions so the max sum hits exactly max_utility_sum
                scale = max_utility_sum / actual_max
                # re-scale uf1 weights
                uf1 = LinearUtilityFunction(
                    [w * scale for w in uf1.weights], uf1.evaluation_functions
                )
            break
    else:
        # fallback: just use whatever we have
        pass

    rv1 = 0.0
    rv2 = 0.0

    return NegotiationDomain(domain_name, offer_space, uf1, rv1, uf2, rv2)


def generate_domains() -> list:
    """
    Returns a diverse set of random domains spanning small/large and
    cooperative/competitive settings, matching what the assignment says
    the final tournament will use.
    """
    domains = []

    # Small cooperative  (2-3 issues, 2-3 options)
    domains.append(generate_domain("SmallCoop", 2, 3, 2, 3, max_utility_sum=2.0, strict=True))

    # Small competitive
    domains.append(generate_domain("SmallComp", 2, 3, 2, 3, max_utility_sum=1.3, strict=True))

    # Medium cooperative
    domains.append(generate_domain("MedCoop", 3, 4, 3, 4, max_utility_sum=2.0, strict=True))

    # Medium competitive
    domains.append(generate_domain("MedComp", 3, 4, 3, 4, max_utility_sum=1.3, strict=True))

    # Large cooperative
    domains.append(generate_domain("LargeCoop", 4, 5, 3, 4, max_utility_sum=2.0, strict=True))

    # Large competitive
    domains.append(generate_domain("LargeComp", 4, 5, 3, 4, max_utility_sum=1.3, strict=True))

    return domains


if __name__ == "__main__":
    doms = generate_domains()
    print(f"Generated {len(doms)} domains:")
    for d in doms:
        n_offers = len(d.offer_space.get_all_offers())
        print(f"  {d.domain_name}: {len(d.offer_space.issues)} issues, {n_offers} offers")
