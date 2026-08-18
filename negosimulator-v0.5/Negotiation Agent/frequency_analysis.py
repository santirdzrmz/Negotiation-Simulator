from domains import EvaluationFunction, LinearUtilityFunction, OfferSpace
from opponent_utility_models import OpponentUtilityModel


class frequencyAnalysis(OpponentUtilityModel):
    
    def __init__(self, offer_space:OfferSpace):

        self.offer_space = offer_space
        self.num_issues = len(offer_space.issues)

        self.approximate_utility_function = None
        self.num_received_proposals = 0

        ## Create a table that will store, for every issue I_j and every option o, the number of times the opponent has proposed an offer
        ## containing that option.
        ## Of course, initially this table will just contain zeros.
        self.freq_table = []
        for i in range(self.num_issues):

            # create a table row to represent Issue i.
            table_row = []

            # Fill the row with just zeros. A zero for each option.
            for o in offer_space.issues[i].options:
                table_row.append(0)

            # Add the row to the table.
            self.freq_table.append(table_row)


   
    def update(self, received_offer, time:float) -> None:

        """ This method should be called every time we receive a new proposal."""
        
        # Update the number of received proposals.
        self.num_received_proposals += 1

        # update the frequency table.
        for i in range(self.num_issues):
            issue = self.offer_space.issues[i]
            
            for o in range(len(issue.options)):
                option = issue.options[o]
                
                if received_offer[i] == option:
                    self.freq_table[i][o] = self.freq_table[i][o] + 1
            
            
        ## Now, use the frequency table to create a new approximation of the opponent's utility function.
        
        
            # First, estimate the weights of the opponent's utility function.
        approx_weights = []
        
        for i in range(self.num_issues):
            issue = self.offer_space.issues[i]

            # For Issue i, determine which how often the most proposed option has been proposed.
            max_freq = 0
            for o in range(len(issue.options)):
                max_freq = max(max_freq, self.freq_table[i][o])

            approx_weights.append(max_freq / self.num_received_proposals)


            # Next, estimate the opponent's evaluation functions.
        approx_evaluation_functions = []
        for i in range(self.num_issues):
            issue = self.offer_space.issues[i]

            approx_evaluations = []

            for o in range(len(issue.options)):
                approx_evaluations.append(self.freq_table[i][o] / self.num_received_proposals)

            approx_evaluation_functions.append(EvaluationFunction(issue, approx_evaluations))


        #TODO: optionally, we could add some more code here to ensure the approximate utility function is normalized.

        self.approximate_utility_function = LinearUtilityFunction(approx_weights, approx_evaluation_functions)

        



    def get_approximate_utility_function(self) -> LinearUtilityFunction|None:
        """Returns None if we have not received any proposals yet."""
        return self.approximate_utility_function