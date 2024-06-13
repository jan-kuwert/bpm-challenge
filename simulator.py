#! /usr/bin/python3
import requests
from enum import Enum, auto
from bottle import run, request, post, get, put, delete
import json
import sqlite3
from datetime import datetime

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
    resources = 4


@post("/patient_admission")
def patient_admission():
    try:
        patientData = {}
        patientData["id"] = request.forms.get("id")
        patientData["type"] = request.forms.get("type")
        if patientData["type"] == "er":
            patientData["treatment"] = "er"
        patientData["admission_time"] = request.forms.get("admission_time")
        if not patientData["admission_time"] or patientData["admission_time"] == None:
            patientData["admission_time"] = datetime.now().strftime(
                "%m/%d/%Y, %H:%M:%S"
            )
        patientData["resources"] = request.forms.get("resources")
        if patientData["resources"] == None and patientData["type"] != "er":
            patientData["resources"] = "intake"
        elif patientData["type"] == "er":
            patientData["resources"] = "er"
        if not patientData["id"]:
            patientData["id"] = add_patient(patientData)
        print("Patient Data:", patientData)
        return patientData
    except Exception as e:
        print("patient_admission_error: ", e)
        return e


@post("/surgery")
def index(patientData):

    return


@post("/nursing")
def index(patientData):

    return


@post("/er")
def index(patientData):

    return


@post("/releasing")
def index(patientData):

    return


@post("/replan_patient")
def index(patientData):

    return


def add_patient(patientData):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO Patients(type, treatment, resources, scheduled)
            VALUES(?, ?, ?, ?)
            """,
            (
                patientData["type"],
                patientData["treatment"],
                patientData["resources"],
                patientData["scheduled"],
            ),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid
    except Exception as e:
        print("add_patient_error: ", e)
    return


def create_database():
    connection = sqlite3.connect("hospital.db")
    cursor = connection.cursor
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Patients(
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL
            admission_time TEXT NOT NULL,
            treatment TEXT,
            resources TEXT,
            scheduled TEXT,
        )
        """
    )
    connection.commit()
    connection.close()


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
