


from abc import abstractmethod


from domains import OfferSpace, UtilityFunction



class OpponentStrategyModel:

    """ Abstract base class for any algorithm to estimate the opponent's strategy. """
    
    @abstractmethod
    def update(self, received_offer, time:float) -> None:
        pass 

    @abstractmethod
    def predict(self, current_time:float, prediction_time:float) -> float:
        
        """ 
        Returns a prediction of the highest utility that the opponent will have proposed to us at the 'prediction time' 
        
        args:
            :param current_time float: The time at which the prediction is made.
            :param prediction_time float: The time for which we are making the prediction
        
        """
        pass




class SimpleOpponentStrategyModel(OpponentStrategyModel):

    """ A very simple algorithm to estimate how far the opponent will be willing to concede. 
        It simply takes the highest utility that the opponent has so far proposed to us, and then makes a linear extrapolation to the deadline.
    """

    def __init__(self, offer_space:OfferSpace, my_utility_function: UtilityFunction):
    
        self.my_utility_function = my_utility_function

        # Determine the highest utility and the lowest utility we can possibly achieve in this domain.
        self.max_utility = -float('inf')
        self.min_utility = float('inf')
        for offer in offer_space.get_all_offers():
            util = my_utility_function.get_utility(offer)
            self.max_utility = max(self.max_utility, util)
            self.min_utility = min(self.min_utility, util)

        # The highest utility we have so far received.
        self.highest_utility_received = -float('inf')


    def update(self, received_offer, time:float) -> None:

        # Calculate the utility of the received offer.
        util_of_received_offer = self.my_utility_function.get_utility(received_offer)

        # Update the highest utility among any received offers.
        self.highest_utility_received = max(self.highest_utility_received, util_of_received_offer)


    def predict(self, current_time:float, prediction_time:float) -> float:
        
        """ 
        Returns a prediction of the highest utility that the opponent will have proposed to us at the 'prediction time' 
        
        args:
            :param current_time float: The time at which the prediction is made.
            :param prediction_time float: The time for which we are making the prediction
        
        """

        #print("predict: current_time: " + str(current_time) + " prediction time: " + str(prediction_time) )
        #print("self.highest_utility_received: " + str(self.highest_utility_received))

        # Extrapolate the hightest utility received so far, to the the prediction time.
        predicted_utility = self.min_utility + (prediction_time / current_time) * (self.highest_utility_received - self.min_utility)

        # Make sure that the predicted utility is not higher than the maximum utility.
        predicted_utility = min(predicted_utility, self.max_utility)

        #print("predicted_utility: " + str(predicted_utility))

        return predicted_utility