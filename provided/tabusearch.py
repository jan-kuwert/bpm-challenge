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
        pass
