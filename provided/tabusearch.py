import random as rd


class TabuSearch:
    def __init__(self, plannable_elements, tabu_tenure=10) -> None:
        """
        :param tabu_tenure: int of how many iterations a move is tabu
        :param current_state: dict of current state of the problem from simulator
        """
        self.tabu_tenure = tabu_tenure
        self.tabu_list = []
        self.initial_solution = self.get_initial_solution()
        self.instance_dict = plannable_elements

    def get_initial_solution(self):
        """
        :return: dict of random initial solution
        """
        rd.shuffle(self.instance_dict)
        return self.instance_dict

    def get_cost(self, current_state):
        """
        :param current_state: dict of current state of the problem from simulator
        :return: int of cost of current state

        Cost:
        if patient planned after 7days make extreme high cost
        make cost less the shorter patient has to wait (expontial: very low for 1/2 days a lot more for 5/6 etc)
        make cost of already replanned patient higher and for multiple replans extreme
        multiply with factor for ER patients
        
        """
        cost = 0
        for i in range(len(current_state)):
            for j in range(i + 1, len(current_state)):
                if current_state[i] > current_state[j]:
                    cost += 1
        return cost
    

    def get_neighbourhood(self, current_state):
        """
        :param current_state: dict of current state of the problem from simulator
        :return: list of all possible moves from current state
        """
        neighbourhood = []
        for i in range(len(current_state)):
            for j in range(i + 1, len(current_state)):
                neighbour = current_state.copy()
                neighbour[i], neighbour[j] = neighbour[j], neighbour[i]
                neighbourhood.append(neighbour)
        return neighbourhood

    def Tsearch(self):
        """
        :return: A list of tuples of how the elements are planned. Each tuple must have the following format: (case_id, element_label, timestamp).
        """
        tenure = self.tabu_tenure
        best_solution = self.initial_solution

