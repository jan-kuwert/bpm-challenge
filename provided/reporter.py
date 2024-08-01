from simulator import EventType
from datetime import datetime, timedelta

import os


class Reporter:

    def __init__(self):
        # The simulation starts at Monday 2018-01-01 00:00:00.000
        # Simulation time is in hours from the initial time	
        self.initial_time = datetime(2018, 1, 1)
        self.time_format = "%Y-%m-%d %H:%M:%S.%f"
    
    def get_formatted_timestamp(self, timestamp):
         return (self.initial_time + timedelta(hours=timestamp)).strftime(self.time_format)

    def callback(self, case_id, element, timestamp, resource, lifecycle_state):
        t = self.get_formatted_timestamp(timestamp)
        if element is not None:
            tt = element.label
            dt = '\t' + '\t'.join(str(v) for v in element.data.values())
        else:
            tt = str(None)
            dt = ""
            return str(case_id) + "\t" + tt + "\t" + t + "\t" + str(resource) + "\t" + str(lifecycle_state) + dt


class EventLogReporter(Reporter):
    """
    This class is used to log the events of the simulation in a CSV file that can be read in a process mining tool.
    The CSV file has a header with the following columns: case_id, task_id, event_label, resource, start_time, completion_time, data_type1, data_type2, ...
    The constructor takes two arguments: the filename of the CSV file and a list of data types that will be logged in the CSV file.
    """
    def __init__(self, filename, data_types):
        super().__init__()
        self.task_start_times = dict()
        self.data_types = data_types

        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        self.logfile = open(filename, "wt")
        self.logfile.write("case_id,task_id,event_label,resource,start_time,completion_time")
        for data_type in data_types:
            self.logfile.write("," + data_type)        
        self.logfile.write("\n")

    def callback(self, case_id, element, timestamp, resource, lifecycle_state):
        if lifecycle_state==EventType.START_TASK:
            self.task_start_times[(case_id, element.label)] = self.get_formatted_timestamp(timestamp)
        elif lifecycle_state==EventType.COMPLETE_EVENT or lifecycle_state==EventType.COMPLETE_TASK:
            completion_time = self.get_formatted_timestamp(timestamp)
            if element.is_task():
                start_time = self.task_start_times[(case_id, element.label)]
                del self.task_start_times[(case_id, element.label)]
            else:
                start_time = completion_time
            resource = resource
            self.logfile.write(str(case_id) + ",")
            self.logfile.write(str(element.id) + ",")
            self.logfile.write(element.label + ",")
            self.logfile.write(str(resource) + ",")
            self.logfile.write(start_time + ",")
            self.logfile.write(completion_time)
            for data_type in self.data_types:
                if data_type in element.data:
                    self.logfile.write("," + str(element.data[data_type]))
                else:
                    self.logfile.write(",")
            self.logfile.write("\n")
            self.logfile.flush()

    def close(self):
        self.logfile.close()