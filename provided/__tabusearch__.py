#!/usr/bin/env python3
import random as rd

from simulator import Simulator
from planners import Planner
from problems import HealthcareProblem, ResourceType
from reporter import EventLogReporter
from simulator import EventType


class TabusearchPlanner(Planner):
    def __init__(self, eventlog_file, data_columns, tabu_tenure=10):
        super().__init__()
        self.eventlog_reporter = EventLogReporter(eventlog_file, data_columns)
        self.planned_patients = set()
        # stores patients
        self.instance_dict = {}
        # stores number resources that are currently in use
        self.used_resources = self.init_resource_dict()
        # stores the number of patients waiting for a resource by resource type
        self.resource_queues = self.init_resource_dict()
        self.tabu_tenure = tabu_tenure

    def report(self, case_id, element, timestamp, resource, lifecycle_state):
        self.eventlog_reporter.callback(
            case_id, element, timestamp, resource, lifecycle_state
        )

        self.instance_dict[case_id] = (
            element,
            timestamp,
            resource,
            lifecycle_state,
        )

        if lifecycle_state == EventType.ACTIVATE_TASK:
            if resource:
                self.resource_queues[resource.type] += 1
        elif lifecycle_state == EventType.START_TASK:
            if resource:
                self.resource_queues[resource.type] -= 1
                self.used_resources[resource.type] += 1
        elif lifecycle_state == EventType.COMPLETE_TASK:
            if resource:
                self.used_resources[resource.type] -= 1
        elif lifecycle_state == EventType.COMPLETE_CASE:
            self.instance_dict.pop(case_id)
            pass

    def plan(self, plannable_elements, simulation_time):
        tenure = self.tabu_tenure
        tabu_list = self.get_tabu_list()

        current_solution = self.get_initial_solution(plannable_elements)
        best_solution = self.get_initial_solution(plannable_elements)
        best_cost = self.get_cost(best_solution)
        

        Terminate = 0
        while Terminate < 100:

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

        return planned_elements

    def init_resource_dict(self):
        """
        :return: dict of all resources with initial values set to 0
        """
        resource_dict = {}
        for resource in ResourceType:
            resource_dict[resource.name] = 0
        return resource_dict

    def get_initial_solution(self, plannable_elements):
        """
        :return: dict of random initial solution
        Convert to list and back to shuffle correct
        since we delete completed instances so not all keys are there
        """
        instances = list(plannable_elements.items())
        rd.shuffle(instances)
        return dict(instances)


planner = TabusearchPlanner("./temp/tabu_event_log.csv", ["diagnosis"])
problem = HealthcareProblem()
simulator = Simulator(planner, problem)
result = simulator.run(1 * 24)

print(result)

# print(self.planner_helper.available_resources()[1])

# def available_resources(self, resource_type="all"):
#     """
#     Returns the number of resources of a specific type that are available.
#     Possible types are "OR", "A_BED", "B_BED".
#     :param resource_type: the type of resources to check for availability.
#     :return: res: all available resources by their id, res_count: the number of available resources counted per resource category
#     """

#     res = []
#     for resource in self.__problem.resources:
#         if self.__problem.resources_available(resource, self.__simulator.now):
#             if resource_type == "all" or resource_type == resource.type:
#                 res.append(resource)
#     res_count = []
#     for resourceType in ResourceType:
#         count = 0
#         for resource in res:
#             if resource.type == resourceType:
#                 count += 1
#         res_count.append((resourceType, count))
#     return res, res_count
