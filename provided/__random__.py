from simulator import Simulator
from planners import Planner
from problems import HealthcareProblem
from reporter import EventLogReporter
import random


class NaivePlanner(Planner):
    def __init__(self, eventlog_file, data_columns):
        super().__init__()
        self.eventlog_reporter = EventLogReporter(eventlog_file, data_columns)
        self.planned_patients = set()

    def report(self, case_id, element, timestamp, resource, lifecycle_state):
        self.eventlog_reporter.callback(
            case_id, element, timestamp, resource, lifecycle_state
        )

    def plan(self, plannable_elements, simulation_time):
        planned_elements = []
        # next_plannable_time = round((simulation_time + 24) * 2 + 0.5) / 2
        for case_id, element_labels in sorted(plannable_elements.items()):
            for element_label in element_labels:
                next_plannable_time = round(
                    simulation_time + random.randint(25, 168)
                )  # improved random replan between 25h and 1 week
                planned_elements.append((case_id, element_label, next_plannable_time))
        return planned_elements


planner = NaivePlanner("./temp/event_log.csv", ["diagnosis"])
problem = HealthcareProblem()
simulator = Simulator(planner, problem)
result = simulator.run(365 * 24)

print(result)
