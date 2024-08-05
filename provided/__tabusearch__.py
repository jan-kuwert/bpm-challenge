from simulator import Simulator
from planners import Planner
from problems import HealthcareProblem
from reporter import EventLogReporter


class TabusearchPlanner(Planner):
    def __init__(self, eventlog_file, data_columns):
        super().__init__()
        self.eventlog_reporter = EventLogReporter(eventlog_file, data_columns)
        self.planned_patients = set()
        self.plannable_time_span = [24, 24 * 7]  # possible plan time 24 hours, 7 days

    def report(self, case_id, element, timestamp, resource, lifecycle_state):
        self.eventlog_reporter.callback(
            case_id, element, timestamp, resource, lifecycle_state
        )

        if lifecycle_state == "":
            self.planned_patients.add(case_id)

    def plan(self, plannable_elements, simulation_time):
        # print(self.planner_helper.available_resources()[1])
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


planner = TabusearchPlanner("./temp/tabu_event_log.csv", ["diagnosis"])
problem = HealthcareProblem()
simulator = Simulator(planner, problem)
result = simulator.run(20 * 24)

print(result)


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
