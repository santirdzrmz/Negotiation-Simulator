

import math
import random

from domains import EvaluationFunction, Issue, LinearUtilityFunction, NegotiationDomain, OfferSpace


def generate_domain(domain_name:str, min_num_issues:int, max_num_issues:int, min_issue_size:int, max_issue_size:int, max_util_sum:float=2.0, strict:bool=False):

    """Returns a randomly generated linear negotiation domain for two agents, with normalized utility functions.
        
        Furthermore, ensures that there is no offer for which u_1(o) + u_2(o) is greater than a specified value.

    Args:
        domain_name: The name of the domain.
        min_num_issues: The minimum number of issues.
        max_num_issues: The maximum number of issues.
        min_issue_size: The minimum size of each issue.
        max_issue_size: The maximum size of each issue.
        max_util_sum: The maximum utility sum (i.e. for all offers o we must have u_1(o) + u_2(o) <= max_util_sum)
        strict: If set to 'True' the max_util_sum will be interpreted as a *strict* upper bound. That is: there will be at least one offer for which u_1(o) + u_2(o) == max_util_sum
    """

    

    if not (1 <= min_num_issues):
        raise Exception("minimum number of issues must be at least 1.")
    if not (min_num_issues <= max_num_issues):
        raise Exception("minimum number of issues must smaller than or equal to maximum number of issues.")
    
    if not (3 <= min_issue_size):
        raise Exception("minimum issue size must be at least 3.")
    if not (min_issue_size <= max_issue_size):
        raise Exception("minimum issue size must smaller than or equal to maximum issue size.")


    if not (1 < max_util_sum):
        raise Exception("Max_util_sum should be at least 1.")
    
    if strict and not (max_util_sum <= 2):
        raise Exception("If the max_util_sum is set as a *strict* upper bound, then it should be at most 2.")

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
    [util_function_1, util_function_2] = generate_utility_Functions(offer_space, max_util_sum, strict)


    # Randomly choose the reservation values (between 0 and 0.4)
    rv_1 = 0.4*random.random()
    rv_2 = 0.4*random.random()

    return NegotiationDomain(domain_name, offer_space, util_function_1, rv_1, util_function_2, rv_2)



def generate_utility_Functions(offer_space:OfferSpace, max_utility_sum:float, strict:bool=True) -> list[LinearUtilityFunction]:

    """
     Generates two utility functions for the given offer space, such that for each offer o we have u_1(o) + u_2(o) <= max_utility_sum.

     The idea is that for each issue i we calculate a number M_i, such that:        <br>
     1)  sum_i M_i = max_util_sum
     2)  for each issue i we have M_i >= max {w_1^i , w_2^i}
    
     Then we use these numbers to ensure that:                      <br>
     3) for each option o of that issue we have   w_1^i * v_1^i(o) + w_2^i * v_2^i(o) <= M_i

      Conditions 1) and 3) ensure that indeed we have u_1(off) + u_2(off) <= max_util_sum  <br>
      Condition 2) is required in order to make condition 3) possible.                      <br>
      After all, there will always be one option o with v_1^i(o) = 1 and one option o with v_2^i(o) = 1  <br>
      So we have at least w_1^i * v_1^i(o) + w_2^i * v_2^i(o) >= max {w_1^i , w_2^i}
    """

    num_issues = len(offer_space.issues)
    
    # 1. Generate random weights.
    
    # In order to satisfy constraint 2), we have to ensure that the following inequality holds (as we will see in the next step)
    # \sum_i  max {w_1^i , w_2^i} <= max_utility_sum
    # where the sum is taken over all issues i.
    
    sum_max_weights = max_utility_sum + 1
    for attempts in range(10_000):

        # 1a. Generate the weights.
        if attempts % 100 == 0:
            weights1 = generate_random_weights(num_issues)
            weights2 = generate_random_weights(num_issues)
            
        # 1b. Ensure the weights are small enough:

        # for each issue, calculate the heighest of the two weights.
        max_weights = [max(weights1[i], weights2[i]) for i in range(num_issues)]

        # Then calculate their sum
        sum_max_weights = sum(max_weights)

        if not (sum_max_weights < max_utility_sum):
            continue


        # 1c. For each issue i calculate the number M_i.
        # The formula below to determine M_i is chosen such that it obviously satisfies condition 1)
        # Note that it only satisfies condition 2) if max_utility_sum / sum_max_weights > 1. That is, if sum_max_weights < max_utility_sum.
        # Indeed, in the previous step we made sure that that condition holds.
        max_util_sum_per_issue = [max_utility_sum * (max_weights[i]/sum_max_weights) for i in range(num_issues)]


        # 1d. Ensure the weights are large enough:
        # In case the maximum util-sum is a strict upper bound, then this is necssesary to guarantee that
        # the upper bound can indeed be attained.
        all_are_large_enough = True
        if strict:
            for i in range(num_issues):
                if not (weights1[i] + weights2[i] >= max_util_sum_per_issue[i]):
                    all_are_large_enough = False
                    break

        if all_are_large_enough:
            break

    if attempts >= 10_000:
        raise Exception("Something is wrong. Can't satisfy the max_utility_sum constraint.")


    eval_functions_1 = [] # Stores, for each issue, the evaluation function of agent 1.
    eval_functions_2 = [] # Stores, for each issue, the evaluation function of agent 2.

    for i in range(num_issues):
        issue = offer_space.issues[i]
        eval_funcs_for_issue = _generate_eval_functions(issue, weights1[i], weights2[i], max_util_sum_per_issue[i], strict)

        eval_functions_1.append(eval_funcs_for_issue[0])
        eval_functions_2.append(eval_funcs_for_issue[1])

    util_function_1 = LinearUtilityFunction(weights1, eval_functions_1)
    util_function_2 = LinearUtilityFunction(weights2, eval_functions_2)

    return [util_function_1, util_function_2]




def _generate_eval_functions(issue:Issue, weight1:float, weight2:float, max_inner_product:float, strict:bool) -> list[EvaluationFunction]:

    issue_size = len(issue.options)

    evaluations_1 = []
    evaluations_2 = []

    
    # Pick an option for which the maximum inner product will be exactly attained (in case strict == True)
    if strict:
        max_option_index = random.randint(1,issue_size-2)
        # TODO: handle the case that issue_size == 2

        # If v1 and v2 can each not be greater than 1, then the maximum 'inner product' we can generate equals w1 * v1 + w2 *v2 = w1 + w2.
        # So, if this is still smaller than the desired inner product, then we have a problem.
        if weight1 + weight2 < max_inner_product:
            raise Exception("Can't satisfy the 'strict' constraint for this issue.")

    else:
        max_option_index = -1
    

    for op in range(issue_size):

        if op==0:
            v1 = 0
            v2 = 1
            
        elif op == issue_size-1:
            v1 = 1
            v2 = 0
                    
        elif op == max_option_index:
            
            [v1, v2] = _find_v(weight1, weight2, max_inner_product)

            # # pick two random numbers v1 and v2, each between 0 and 1, and such that w1*v1 + w2*v2 == max_inner_product
            # v1 = random.random()
            # v2 = random.random()
            # ip = weight1*v1 + weight2*v2

            # v1 *= (max_inner_product/ip)
            # v2 *= (max_inner_product/ip)

            if abs(weight1*v1 + weight2*v2 - max_inner_product) > 0.01:
                raise Exception("Error 0")

            if v1 > 1: 

                raise Exception("Error 1")

            if v2 > 1:
                raise Exception("Error 2")

        else:
            
            # pick two random numbers v1 and v2, each between 0 and 1, and such that w1*v1 + w2*v2 < max_sum
            v1 = random.random()
            v2 = random.random()
            ip = weight1*v1 + weight2*v2

            if ip > max_inner_product:
                v1 *= (max_inner_product/ip)
                v2 *= (max_inner_product/ip)

        evaluations_1.append(round(v1,3))
        evaluations_2.append(round(v2,3))

        if weight1*v1 + weight2*v2 - max_inner_product > 0.01:
            raise Exception("ERROR" )

    #2 Create the Evaluation functions and add return them.
    evaluation_function_1 = EvaluationFunction(issue, evaluations_1)
    evaluation_function_2 = EvaluationFunction(issue, evaluations_2)


    
    return [evaluation_function_1, evaluation_function_2]
       


def generate_random_weights(num_issues:int):
    
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

    # If any of the weights is too small, then repeat.
    min_weight = min(weights)
    if min_weight < 0.01:
        weights = generate_random_weights(num_issues)

    # This shouldn't happen, but just in case.
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



def _inner_product(w:list[float], v:list[float]):
    return w[0]*v[0] + w[1]*v[1]

def _norm(a):
    return math.sqrt(a[0]**2 + a[1]**2)

def _find_v(w1:float, w2:float, desired_inner_product:float):

    w = [w1, w2]
    target = [0.5, 0.5]

    # Feasibility check
    if desired_inner_product < 0 or desired_inner_product > w1 + w2:
        raise ValueError("No solution exists within [0,1]^2")

    # Handle zero vector
    if abs(w1) < 1e-12 and abs(w2) < 1e-12:
        raise ValueError("No solution exists")

    # Projection of (0.5,0.5) onto line w·v = c
    w_dot_w = _inner_product(w, w)
    lambda_ = (_inner_product(w, target) - desired_inner_product) / w_dot_w
    v = [target[0] - lambda_ * w[0],
            target[1] - lambda_ * w[1]]

    # Clip to [0,1]
    v = [min(1, max(0, v[0])), min(1, max(0, v[1]))]

    # Check if still satisfies constraint
    if abs(_inner_product(w, v) - desired_inner_product) < 1e-9:
        return v

    candidates = []

    # Fix v1 = 0 or 1
    for v1 in [0.0, 1.0]:
        if abs(w2) > 1e-12:
            v2 = (desired_inner_product - w1 * v1) / w2
            if 0 <= v2 <= 1:
                candidates.append([v1, v2])

    # Fix v2 = 0 or 1
    for v2 in [0.0, 1.0]:
        if abs(w1) > 1e-12:
            v1 = (desired_inner_product - w2 * v2) / w1
            if 0 <= v1 <= 1:
                candidates.append([v1, v2])

    # Include clipped projection as fallback
    candidates.append(v)

    # Pick closest to (0.5,0.5)
    best = min(candidates, key=lambda x: _norm([x[0] - 0.5, x[1] - 0.5]))

    return best


if __name__=='__main__':

    domain = generate_domain("test", 3, 8, 3, 8, 1.2, True)

    # calculate the max-sum:

    max_sum = max(domain.utility_functions[0].get_utility(offer) + domain.utility_functions[1].get_utility(offer) for offer in domain.offer_space.get_all_offers())
    print("MAX SUM: " + str(max_sum))


    for u in domain.utility_functions:

        if not isinstance(u, LinearUtilityFunction):
            raise Exception()
        
        print()
        print("Utility function: ")
        for i in range(len(domain.offer_space.issues)):
            
            issue = domain.offer_space.issues[i]

            print(issue.name + " w=" + str(u.weights[i]) + " evals=" + str(u.evaluation_functions[i].eval_func))

