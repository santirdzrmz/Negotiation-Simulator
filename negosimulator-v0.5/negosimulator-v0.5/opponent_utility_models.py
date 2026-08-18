


from abc import abstractmethod
import random

from domains import EvaluationFunction, LinearUtilityFunction, OfferSpace


class OpponentUtilityModel:

    """ Abstract base class for any algorithm to estimate the opponent's utility function. """

    @abstractmethod
    def update(self, received_offer, time:float) -> None:
        pass


    @abstractmethod
    def get_approximate_utility_function(self) -> LinearUtilityFunction:
        pass




class DummyOpponentUtilityModel(OpponentUtilityModel):

    """
    This is a 'fake' opponent modeling algorithm that you can use if you haven't implemented any real opponent modeling algorithm yet.
    It is fake in the sense that it requires the true utility function of the opponent as input, and returns an approximation of that utility function.
    
    Of course, in a real negotiation you wouldn't have access to the opponent's utility function, and even if you did have access to it, then you wouldn't
    need any opponent modeling algorithm in the first place.

    Therefore, this opponent model can only be used as a simulation of a real opponent model.
    """
    

    def __init__(self, offer_space:OfferSpace, true_opponent_utility_function:LinearUtilityFunction):
        
        APROXIMATION_ACCURACY = 0.10

        num_issues = len(true_opponent_utility_function.weights)
        
        # To get the approximated weights, multiply the true weights of the opponent with a random value between 0.90 and 1.10
        
        approx_weights = []
        for i in range(num_issues):

            r = random.uniform(1-APROXIMATION_ACCURACY, 1+APROXIMATION_ACCURACY)
            approx_weights.append(r * true_opponent_utility_function.weights[i])


        # To get the approximated evaluation functions, for each issue, multiply the true evaluations of every option with a random value between 0.90 and 1.10
       
        approx_evaluation_functions = []
        for i in range(num_issues):
        
            issue = offer_space.issues[i]
            true_eval_function = true_opponent_utility_function.evaluation_functions[i]

            approx_evaluations = []

            for j in range(len(issue.options)):

                option = issue.options[j]

                r = random.uniform(1-APROXIMATION_ACCURACY, 1+APROXIMATION_ACCURACY)
                approx_evaluations.append(r * true_eval_function.get_evaluation(option))

            approx_evaluation_functions.append(EvaluationFunction(issue, approx_evaluations))


        self.approximate_utility_function = LinearUtilityFunction(approx_weights, approx_evaluation_functions)

        

    def get_approximate_utility_function(self):
        """Returns a utility function that is an approximation of the opponent's utility function."""
        return self.approximate_utility_function

    def update(self, received_offer, time):
        # This dummy opponent model doesn't need to be updated.
        pass