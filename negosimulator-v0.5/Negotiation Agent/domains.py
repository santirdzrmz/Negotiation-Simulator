from abc import abstractmethod
import json
from os import listdir
from os.path import isfile, join
import random
import itertools

class Issue:

    def __init__(self, name: str, options: list[str]):
        self.name = name
        self.options = options

    def __eq__(self, other):
        return self.name == other.name and self.options == other.options

class OfferSpace:

    def __init__(self, issues: list[Issue]):
        self.issues = issues

    def get_all_offers(self) -> list[tuple[str]]:

        """ Returns a list containing all offers in the domain. Each offer is a tuple of strings."""

        # first create a list of lists, in which each list is the list of options of that issue.
        # e.g. [[Volvo, Ford, Ferrari], [red, yellow, green]]
        list_of_lists = []
        for issue in self.issues:
            list_of_lists.append(issue.options)


        # next, create the cartesian products of those lists.
        # e.g. [[Volvo, red], [Volvo, yellow], [Volvo, green], [Ford, red], [Ford, yellow], [Ford, green], [Ferrari, red], [Ferrari, yellow], [Ferrari, green]]     
        all_offers =  list(itertools.product(*list_of_lists))

        return all_offers
    
    def __eq__(self, other):
        return self.issues == other.issues


class EvaluationFunction:

    """
    A function that assigns, for each option of a given issue, an 'evaluation value'
    """

    def __init__(self, issue: Issue, evaluations: list[float]):
        self.eval_func = dict(zip(issue.options, evaluations))

    def get_evaluation(self, option:str) -> float:
        return self.eval_func[option]

    
class UtilityFunction:

    @abstractmethod
    def get_utility(self, offer: tuple[str])-> float:
        pass



class LinearUtilityFunction(UtilityFunction):

    def __init__(self, weights:list[float], evaluation_functions:list[EvaluationFunction]):
        
        if len(weights) != len(evaluation_functions):
            raise ValueError("Number of weights is not equal to the number of evaluation functions.")

        self.num_issues:int = len(weights)      
        
        self.weights:list[float] = weights
        self.evaluation_functions:list[EvaluationFunction] = evaluation_functions
       
        

    def get_utility(self, offer: tuple[str])-> float:

        utility_value = 0
        
        for i in range(self.num_issues):
            utility_value += self.weights[i] * self.evaluation_functions[i].get_evaluation(offer[i])

        return utility_value


class NegotiationDomain:

    def __init__(self, 
                 domain_name: str,
                 offer_space: OfferSpace, 
                 utility_function_1:UtilityFunction, 
                 reservation_value_1:float,
                 utility_function_2:UtilityFunction,
                reservation_value_2:float ):
        
        self.domain_name = domain_name
        self.offer_space = offer_space
        self.utility_functions = [utility_function_1, utility_function_2]
        self.reservation_values = [reservation_value_1 , reservation_value_2]



def get_example_domain() -> NegotiationDomain:


    """ Returns a very small bilateral negotiation domain with linear utility functions.
     This domain represents the negotiations between a husband and wife that aim to buy a car together.
    Specifically, they are negotiating about two issues: which brand of car they should buy and which color the car should have."""

    ## 1. CREATE THE OFFER SPACE
    issue1 = Issue("Brand", ["Volvo", "Ford", "Ferrari"])
    issue2 = Issue("Color", ["red", "yellow", "green"])

    offer_space = OfferSpace([issue1, issue2])
   

    ## 3. CREATE THE UTILITY FUNCTION FOR AGENT 1.
        # Note: to ensure the utility function is normalized, make sure that for each issue there is at least one option
        # that has evaluation 0 and at least one option that has evaluation 1. All other options should have an evaluation in the interval [0,1]
        # Furthermore, also make sure the weights add up to 1.
    weight_1_1 = 0.5
    evaluation_function_1_1 = EvaluationFunction(issue1, [0, 0.3, 1])
    weight_1_2 = 0.5
    evaluation_function_1_2 = EvaluationFunction(issue2, [0, 0.6, 1])
   

    linear_utility_function_1 = LinearUtilityFunction([weight_1_1,weight_1_2],[evaluation_function_1_1, evaluation_function_1_2])

    reservation_value_1 = 0.0

    ## 4. CREATE THE UTILITY FUNCTION FOR AGENT 2.
    weight_2_1 = 0.3
    evaluation_function_2_1 = EvaluationFunction(issue1, [1, 0.2, 0])
    weight_2_2 = 0.7
    evaluation_function_2_2 = EvaluationFunction(issue2, [0.4, 1, 0])
    

    linear_utility_function_2 = LinearUtilityFunction([weight_2_1,weight_2_2], [evaluation_function_2_1, evaluation_function_2_2])

    reservation_value_2 = 0.0

    # 4. PUT THESE COMPONENTS TOGETHER INTO A SINGLE NegotiationDomain OBJECT    
    domain = NegotiationDomain("Car Sale", offer_space, 
                                linear_utility_function_1, reservation_value_1, 
                                linear_utility_function_2, reservation_value_2)

    return domain


def load_domain_from_folder(folderpath:str) -> NegotiationDomain:   
    
    """Assumes the folder contains exactly two json files, each representing one utility function for the same offer space."""

    # Collect the paths af all .json files in the given folder.
    jsonfiles = [join(folderpath, f) for f in listdir(folderpath) if isfile(join(folderpath, f)) and f.endswith(".json")]

    # Check that there are exactly two of them.
    if len(jsonfiles) != 2:
        raise Exception("The number of json files in the folder should be 2. However, it contains the following files: " + str(jsonfiles))

    # Ensure the files are listed in alphabetical order, so that we always generate exactly the same negotiation domain.
    jsonfiles.sort()


    # Parse the two respective files.
    [domain_name_1, offer_space_1, util_1, rv_1] = load_util_function_from_file(jsonfiles[0])
    [domain_name_2, offer_space_2, util_2, rv_2] = load_util_function_from_file(jsonfiles[1]) 

    # Check that both files define exactly the same offer space.
    if offer_space_1 != offer_space_2:
        raise Exception("The two offer spaces defined in the two respective json files are not equal. Please check that all issues and options have identical names and that all issues and options appear in exactly the same order in the two files.")
    
    # Check that both files define exactly the same name for the domain.
    if domain_name_1 != domain_name_2:
        raise Exception("The two files contain domains with different names: " + domain_name_1 + " and " + domain_name_2)



    # Finally, put the offer space and the two utility functions all together in a Negotiation Domain object.
    negotiation_domain = NegotiationDomain(domain_name_1, offer_space_1, util_1, rv_1, util_2, rv_2)

    return negotiation_domain
    




def load_util_function_from_file(path_to_json_file:str) -> list:   
    
    ## TODO: for each attribute, check that it is indeed present in the json and, if not, raise an exception.


    with open(path_to_json_file) as f:
        
        json_file_as_dictionary = json.load(f)

        # 1. Parse the domain name
        domain_name:str = json_file_as_dictionary.get("domain_name")

        #2. Parse all issues and their corresponding weights and evaluation functions.
        issues:list[Issue] = []
        weights:list[float] = []
        evaluation_functions:list[EvaluationFunction] = []

        for issue_as_dictionary in json_file_as_dictionary.get("issues"):

            # 2a. Parse the name of the issue.
            issue_name = issue_as_dictionary.get("issue_name")

            # 2b. Parse the list of options of this issue.
            options_as_dict = issue_as_dictionary.get("options")         

            # 2c. From each object in this list parse the name of the option itself and its evaluation.
            options:list[str] = []
            evaluations:list[float] = []
            for option_as_dict in options_as_dict:
                
                option:str = option_as_dict.get("option")
                options.append(option)

                evaluation = float(option_as_dict.get("evaluation"))
                evaluations.append(evaluation)

            # 2d. Create the Issue object
            issue = Issue(issue_name, options)
            issues.append(issue)

            # 2e. Parse the issue weight.
            issue_weight = float(issue_as_dictionary.get("issue_weight"))
            weights.append(issue_weight)

            # 3. Parse the EvaluationFunction
            evaluation_function = EvaluationFunction(issue, evaluations)
            evaluation_functions.append(evaluation_function)


        # Create the OfferSpace object.
        offer_space = OfferSpace(issues)

        # Create the UtilityFunction object.
        linear_utility_function = LinearUtilityFunction(weights,evaluation_functions)
        
        # Parse the reservation value
        rv = float(json_file_as_dictionary.get("reservation_value"))

        return [domain_name, offer_space, linear_utility_function, rv]


    

if __name__== "__main__":

    # TODO: remove this.

    nego_domain:NegotiationDomain = load_domain_from_folder("Domains/Cinema Date/")

    for offer in nego_domain.offer_space.get_all_offers():
        print(str(offer) + " -- " + str(nego_domain.utility_functions[0].get_utility(offer)) + " , " + str(nego_domain.utility_functions[1].get_utility(offer)))

    print("Reservation values: " + str(nego_domain.reservation_values))