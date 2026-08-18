
import matplotlib.pyplot as plt

import domain_generator_2
from domains import NegotiationDomain



#################################################################
# Note: to be able to run this code, you need to have installed the matplotlib library:
# pip install matplotlib
#################################################################

def visualize(domain:NegotiationDomain):

    domain_size = len(domain.offer_space.get_all_offers())

    if domain_size > 1_000_000:
        raise Exception("Domain too large to visualize")

    x_coordinates = [domain.utility_functions[0].get_utility(offer) for offer in domain.offer_space.get_all_offers()]
    y_coordinates = [domain.utility_functions[1].get_utility(offer) for offer in domain.offer_space.get_all_offers()]

    plt.plot(x_coordinates, y_coordinates, 'o')

    plt.show()



if __name__ == "__main__":
    domain = domain_generator_2.generate_domain("test", 3, 8, 3, 8, 1.5, True)

    visualize(domain)


    
