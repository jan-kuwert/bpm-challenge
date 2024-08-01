from simulator import Simulator
from planners import Planner
from problems import HealthcareProblem
from reporter import EventLogReporter
from problems import ResourceType

class TabusearchPlanner(Planner):
    def __init__(self, eventlog_file, data_columns):
        super().__init__()
        self.eventlog_reporter = EventLogReporter(eventlog_file, data_columns)
        self.planned_patients = set()

    def report(self, case_id, element, timestamp, resource, lifecycle_state):
        self.eventlog_reporter.callback(
            case_id, element, timestamp, resource, lifecycle_state
        )

    def plan(self, plannable_elements, simulation_time):
        print(self.planner_helper.available_resources()[1])
        planned_elements = []
        next_plannable_time = round((simulation_time + 24) * 2 + 0.5) / 2
        for case_id, element_labels in sorted(plannable_elements.items()):
            for element_label in element_labels:
                print(element_label)
                planned_elements.append((case_id, element_label, next_plannable_time))
        return planned_elements


planner = TabusearchPlanner("./temp/tabu_event_log.csv", ["diagnosis"])
problem = HealthcareProblem()
simulator = Simulator(planner, problem)
result = simulator.run(1 * 24)

print(result)
