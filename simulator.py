#! /usr/bin/python3
import requests
from enum import Enum, auto
from bottle import route, run, template, post, get, put, delete

resources = {
    "intake": {"current": 1, "max": 1},
    # "intake": {"current": 4, "max": 4},
    # "surgery": {"current": 5, "max": 5},
    # "nursing": {"a": {"current": 30, "max": 30}, "b": {"current": 40, "max": 40}},
    # "er": {"current": 9, "max": 9},
}


class TaskType(Enum):
    patient_admission = auto()
    er_treatment = auto()
    intake = auto()
    surgery = auto()
    nursing = auto()
    releasing = auto()
    replan_patient = auto()


class InstanceType(Enum):
    fork_running = auto()
    fork_ready = auto()
    wait_running = auto()
    wait_ready = auto()


class PatientType(Enum):
    a = auto()
    b = auto()
    er = auto()


class SimulatorTask:
    def __init__(self, type: TaskType, patient, resources: TaskType, duration):
        self.type = type
        self.patient = patient
        self.resources = resources
        self.duration = duration

    def __str__(self):
        return (
            f"Task: {self.type}, Resources: {self.resources}, Duration: {self.duration}"
        )


class simulator:
    def __init__(self, resources):
        self.resources = resources


@get("/names/<name>")
def index(name):
    return template("<b>Hello {name} </>!", name=name)


@get("/intake")
def index():

    return


def new_instance(behavior: InstanceType = "fork_running", type="A"):
    url = "https://cpee.org/flow/start/url/"
    xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
    data = {"behavior": behavior, "url": xml_url, "init": {"type": type}}

    response = requests.post(url, data=data)
    # json_response = response.read()
    # json_response = json.loads(response)
    # instance = json_response['CPEE_INSTANCE']
    print("Respone:", response.response)


new_instance()

run(host="::1", port=23453)
