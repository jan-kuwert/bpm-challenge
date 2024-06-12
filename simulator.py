#! /usr/bin/python3
import requests
from enum import Enum, auto
from bottle import run, request, post, get, put, delete
import json

patientIds = 0
patientQueue = []

# add patient Types with their time values distributions from table

resources = {
    "intake": {"current": 1, "max": 1},
    # "intake": {"current": 4, "max": 4},
    # "surgery": {"current": 5, "max": 5},
    # "nursing": {"a": {"current": 30, "max": 30}, "b": {"current": 40, "max": 40}},
    # "er": {"current": 9, "max": 9},
}


class TaskType(Enum):
    patient_admission = 1
    er = 2
    intake = 3
    surgery = 4
    nursing = 5
    releasing = 6
    replan_patient = 7


class InstanceType(Enum):
    fork_running = 1
    fork_ready = 2
    wait_running = 3
    wait_ready = 4


class PatientType(Enum):
    a = 1
    b = 2
    er = 3


class PatientData(Enum):
    id = 1
    type = 2
    treatment = 3
    resources = []


class SimulatorTask:
    def __init__(
        self, type: TaskType, patient: PatientData, resources: TaskType, duration
    ):
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


@post("/patient_admission")
def patient_admission():
    try:
        patientData = {}
        patientData['id'] = request.forms.get("id")
        patientData['type'] = request.forms.get("type")
        print("data", patientData['id'], patientData['id'] == Null)
        if patientData['id'] == Null:
            global patientIds
            patientData['id'] = patientIds
            patientIds += 1
        if PatientType == 'er':
            patientData['treatment'] = 'er'
        else:
            patientQueue.append(patientData)
            patientData.treatment = TaskType.replan_patient
        return patientData
    except Exception as e:
        print(e)
        return e


@post("/surgery/<patientData>")
def index(patientData):

    return


@post("/nursing/<patientData>")
def index(patientData):

    return


@post("/er/<patientData>")
def index(patientData):

    return


@post("/releasing/<patientData>")
def index(patientData):

    return


@post("/replan_patient/<patientData>")
def index(patientData):

    return


def new_instance(type: PatientType, behavior: InstanceType = "fork_running"):
    url = "https://cpee.org/flow/start/url/"
    xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
    data = {"behavior": behavior, "url": xml_url, "init": {"type": type}}

    response = requests.post(url, data=data)
    # json_response = response.read()
    # json_response = json.loads(response)
    # instance = json_response['CPEE_INSTANCE']
    print("Respone:", response.response)


# new_instance()

run(host="::1", port=23453)
