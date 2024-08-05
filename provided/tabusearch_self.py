import random as rd
from itertools import combinations


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

    def get_tabu_list(self):
        dict = {}
        for swap in combinations(self.instance_dict.keys(), 2):
            dict[swap] = {"tabu_time": 0, "MoveValue": 0}
        return dict

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

    def SwapMove(self, solution, i, j):
        """
        Takes a list (solution)
        returns a new neighbor solution with i, j swapped
        """
        solution = solution.copy()

        i_index = solution.index(i)
        j_index = solution.index(j)

        solution[i_index], solution[j_index] = solution[j_index], solution[i_index]
        return solution

    def Tsearch(self):
        """
        :return: A list of tuples of how the elements are planned. Each tuple must have the following format: (case_id, element_label, timestamp).
        """
        tenure = self.tabu_tenure
        best_solution = self.initial_solution
        current_solution = self.initial_solution
        best_cost = self.get_cost(best_solution)
        tabu_list = self.get_tabu_list()

        iter = 1
        Terminate = 0

        while Terminate < 5:

            for move in tabu_list:
                candidate_solution = self.SwapMove(current_solution, move[0], move[1])
                candidate_cost = self.get_cost(candidate_solution)
                tabu_list[move]["MoveValue"] = candidate_cost

            while True:
                best_move = min(tabu_list, key=lambda x: tabu_list[x]["MoveValue"])
                MoveValue = tabu_list[best_move]["MoveValue"]
                tabu_time = tabu_list[best_move]["tabu_time"]

                if tabu_time < iter:
                    current_solution = self.SwapMove(
                        current_solution, best_move[0], best_move[1]
                    )
                    current_cost = self.Objfun(current_solution)

                    if MoveValue < best_cost:
                        best_solution = current_solution
                        best_cost = current_cost
                        print(
                            "   best_move: {}, Cost: {} => Best Improving => Admissible".format(
                                best_move, current_cost
                            )
                        )
                        Terminate = 0
                    else:
                        print(
                            "   ##Termination: {}## best_move: {}, Cost: {} => Least non-improving => "
                            "Admissible".format(Terminate, best_move, current_cost)
                        )
                        Terminate += 1

                    tabu_list[best_move]["tabu_time"] = iter + tenure
                    iter += 1
                    break
                else:
                    if MoveValue < best_cost:

                        current_solution = self.SwapMove(
                            current_solution, best_move[0], best_move[1]
                        )
                        current_cost = self.Objfun(current_solution)
                        best_solution = current_solution
                        best_cost = current_cost
                        print(
                            "   best_move: {}, Cost: {} => Aspiration => Admissible".format(
                                best_move, current_cost
                            )
                        )
                        Terminate = 0
                        iter += 1
                        break
                    else:
                        tabu_list[best_move]["MoveValue"] = float("inf")
                        print(
                            "   best_move: {}, Cost: {} => Tabu => Inadmissible".format(
                                best_move, current_cost
                            )
                        )
                        continue
        print(
            "#" * 50,
            "Performed iterations: {}".format(iter),
            "Best found Solution: {} , Cost: {}".format(best_solution, best_cost),
            sep="\n",
        )
        return tabu_list, best_solution, best_cost
