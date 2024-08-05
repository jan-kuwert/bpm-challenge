from simulator import Simulator
from planners import Planner
from problems import HealthcareProblem, ResourceType
from reporter import EventLogReporter
import random as rd
from simulator import EventType


class TabusearchPlanner(Planner):
    def __init__(self, eventlog_file, data_columns):
        super().__init__()
        self.eventlog_reporter = EventLogReporter(eventlog_file, data_columns)
        self.planned_patients = set()
        # stores patients
        self.instance_dict = {}
        # stores resources that are currently in use
        self.used_resources = {}
        # stores the number of patients waiting for a resource by resource type
        self.resource_queues = {}
        print(EventType)

    def report(self, case_id, element, timestamp, resource, lifecycle_state):
        self.eventlog_reporter.callback(
            case_id, element, timestamp, resource, lifecycle_state
        )

        if lifecycle_state == EventType.CASE_ARRIVAL:
            self.instance_dict[case_id] = (
                element,
                timestamp,
                resource,
                lifecycle_state,
            )
        elif lifecycle_state == EventType.START_TASK:
            self.task_start_times[case_id] = timestamp
        elif (
            lifecycle_state == EventType.COMPLETE_TASK
            or lifecycle_state == EventType.COMPLETE_EVENT
        ):
            self.task_end_times[case_id] = timestamp
        elif lifecycle_state == EventType.SCHEDULE_RESOURCES:
            pass
        elif lifecycle_state == EventType.ASSIGN_RESOURCES:
            pass

    def plan(self, plannable_elements, simulation_time):
        current_solution = self.get_initial_solution()

        for item in plannable_elements.items():
            print(
                item,
                self.planner_helper.get_case_type(item[0]),
                self.planner_helper.get_case_data(item[0]),
            )

        planned_elements = []
        next_plannable_time = round((simulation_time + 24) * 2 + 0.5) / 2
        for case_id, element_labels in sorted(plannable_elements.items()):
            for element_label in element_labels:
                planned_elements.append((case_id, element_label, next_plannable_time))
        return planned_elements

    def get_initial_solution(self):
        """
        :return: dict of random initial solution
        """
        rd.shuffle(self.instance_dict)
        return self.instance_dict


planner = TabusearchPlanner("./temp/tabu_event_log.csv", ["diagnosis"])
problem = HealthcareProblem()
simulator = Simulator(planner, problem)
result = simulator.run(20 * 24)

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
