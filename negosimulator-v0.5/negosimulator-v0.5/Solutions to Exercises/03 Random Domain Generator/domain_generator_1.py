


import random

from domains import EvaluationFunction, Issue, LinearUtilityFunction, NegotiationDomain, OfferSpace


def generate_domain(domain_name:str, min_num_issues:int, max_num_issues:int, min_issue_size:int, max_issue_size:int):

    """Returns a randomly generated linear negotiation domain for two agents, with normalized utility functions.

    Args:
        domain_name: The name of the domain.
        min_num_issues: The minimum number of issues.
        max_num_issues: The maximum number of issues.
        min_issue_size: The minimum size of each issue.
        max_issue_size: The maximum size of each issue.
    """

    if not (1 <= min_num_issues):
        raise Exception("minimum number of issues must be at least 1.")
    if not (min_num_issues <= max_num_issues):
        raise Exception("minimum number of issues must smaller than or equal to maximum number of issues.")
    
    if not (2 <= min_issue_size):
        raise Exception("minimum issue size must be at least 2.")
    if not (min_issue_size <= max_issue_size):
        raise Exception("minimum issue size must smaller than or equal to maximum issue size.")


    # Randomly choose the number of issues.
    num_issues = random.randint(min_num_issues, max_num_issues)

    # For each issue, randomly choose the number of options for that issue.
    issue_sizes = []
    for _ in range(num_issues):
        issue_size = random.randint(min_issue_size, max_issue_size)
        issue_sizes.append(issue_size)
    
    # Generate the offer space
    offer_space = generate_offer_space(issue_sizes)

    # Randomly generate two utility functions.
    util_function_1 = generate_utility_Function(offer_space)
    util_function_2 = generate_utility_Function(offer_space)

    # Randomly choose the reservation values (between 0 and 0.4)
    rv_1 = 0.4*random.random()
    rv_2 = 0.4*random.random()

    return NegotiationDomain(domain_name, offer_space, util_function_1, rv_1, util_function_2, rv_2)





def generate_utility_Function(offer_space:OfferSpace) -> LinearUtilityFunction:
    
    num_issues = len(offer_space.issues)

    # Generate random weights.
    weights = generate_random_weights(num_issues)

    # Now, for each issue, generate an evaluation function.
    evaluation_functions = []
    for issue in offer_space.issues:
        
        issue_size = len(issue.options)

        # 1. Create n evaluations (where n is the number of options)

        # 1a. First, randomly generate n-2 evaluations.
        evaluations = [round(random.random(),2) for _ in range(issue_size - 2)]

        # 1b. Next, add the values 0 and 1.
        evaluations.append(0)
        evaluations.append(1)

        # 1c. Shuffle them randomly.
        random.shuffle(evaluations)

        #2 Create the Evaluation function and add it to the list.
        evaluation_function = EvaluationFunction(issue, evaluations)
        evaluation_functions.append(evaluation_function)

    # Combine all evaluation functions into a linear utility function.
    linear_utility_function = LinearUtilityFunction(weights,evaluation_functions)

    return linear_utility_function


def generate_random_weights(num_issues):
    
    """ Generates a random vector of weights, such that the sum of all weights equals 1, and such that
        the vector is drawn from a uniform probability distribution over the set of all such vectors ('the unit simplex')
        
        This implementation is based on the 'stick-breaking method':
        
        1. Generate n-1 random numbers uniformly in [0,1]
        2. Sort them in ascending order.
        3. Let the differences between consecutive numbers (including 0 and 1 at the ends) be the weights.
        
        """
    
    # Step 1: generate n-1 uniform numbers
    u = [round(random.random(),2) for _ in range(num_issues - 1)]
    
    # Step 2: sort them
    u.sort()
    
    # Step 3: compute differences
    weights = []
    weights.append(u[0])  # first component
    for i in range(1, num_issues - 1):
        weights.append(u[i] - u[i - 1])
    weights.append(1 - u[-1])  # last component
    
    weights = [round(w,2) for w in weights]

    if sum(weights) < 0.999:
        raise Exception("sum of weights == " + str(sum(weights)))

    return weights


def generate_offer_space(issue_sizes:list[int]) -> OfferSpace:
    
    """Creates an offer space with the given issue sizes. The issues and the options will have default names."""

    ## 1. CREATE THE OFFER SPACE
    num_issues = len(issue_sizes)
    issues = []
    for i in range(num_issues):

        # Create the options for issue i
        size = issue_sizes[i]
        options = ["Option_" + str(i) +"_" + str(j) for j in range(size)]
        
        # Create the issue and add it to the list of all issues.
        issue = Issue("Issue_" + str(i), options)
        
        issues.append(issue)

    # Create the offer space.
    offer_space = OfferSpace(issues)

    return offer_space





if __name__ == '__main__':
    
    domain = generate_domain("test", 3, 8, 2, 8)

    for u in domain.utility_functions:

        if not isinstance(u, LinearUtilityFunction):
            raise Exception()
        
        print()
        print("Utility function: ")
        for i in range(len(domain.offer_space.issues)):
            
            issue = domain.offer_space.issues[i]

            print(issue.name + " w=" + str(u.weights[i]) + " evals=" + str(u.evaluation_functions[i].eval_func))

