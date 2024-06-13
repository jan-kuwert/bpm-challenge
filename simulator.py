#! /usr/bin/python3
import json
import sqlite3
import requests
import numpy as np
from enum import Enum, auto
from datetime import datetime
from pyprobs import Probability as pr
from bottle import run, request, post, get, put, delete

# for now in here
RESOURCES = [
    {"name": "intake", "current": 4, "max": 4},
    {"name": "surgery", "current": 5, "max": 5},
    {"name": "nursing_a", "current": 30, "max": 30},
    {"name": "nursing_b", "current": 40, "max": 40},
    {"name": "em", "current": 9, "max": 9},
]

PATIENT_IDS = 0
PATIENT_QUEUE = []
CURRENT_TIME = 60 * 8  # 8:00 AM
INSTANCE_TYPES = ["fork_running", "fork_ready", "wait_running", "wait_ready"]
DIAGNOSIS_TYPES = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]
PATIENT_TYPES = ["A", "B", "EM"]
INTAKE_TIME = [1, 0.125]
SURGERY_TIME = [
    [0, 0],
    [1, 0.25],
    [2, 0.5],
    [4, 0.5],
    [0, 0],
    [0, 0],
    [4, 0.5],
    [4, 1],
]
NURSING_TIME = [[4, 0.5], [8, 2], [16, 2], [16, 2], [8, 2], [16, 2], [16, 4], [16, 4]]
EMERGENCY_TIME = [2, 0.5]


@post("/patient_admission")
def patient_admission():
    try:
        patientData = {}
        patientData["id"] = request.forms.get("id")
        if not patientData["id"]:
            patientData["type"] = request.forms.get("type")
            patientData["scheduled"] = "false"
            patientData["start_time"] = CURRENT_TIME
            patientData["total_time"] = 0  # tracks time spent in hospital
            patientData["diagnosis"] = request.forms.get("diagnosis")
            patientData["admission_time"] = request.forms.get("admission_time")
            if not patientData["admission_time"]:
                patientData["admission_time"] = datetime.now().strftime(
                    "%m/%d/%Y, %H:%M:%S"
                )
            patientData["resources"] = request.forms.get("resources")
            if patientData["resources"] == None and patientData["type"] != "EM":
                patientData["resources"] = "intake"
            elif patientData["type"] == "EM":
                patientData["resources"] = "EM"
            patientData["resources_available"] = True  # TODO implement
            patientData["id"] = add_patient(patientData)
        else:
            patientData = get_patient(patientData["id"])

        print("Patient Data:", patientData)
        return patientData
    except Exception as e:
        print("patient_admission_error: ", e)
        return e


@post("/replan_patient")
def replan_patient():
    try:
        patientData = get_patient(request.forms.get("id"))
        patientData["scheduled"] = "true"
        patientData["start_time"] = (
            CURRENT_TIME + 12 * 60
        )  # TODO add smart time decision here
        # response = create_instance(patientData) # TODO implement new instance management
        response = True
        set_patient(patientData)
        print("Patient Replanned:", patientData)
        return response
    except Exception as e:
        print("replan_patient_error: ", e)
        return e


@post("/intake")
def intake():
    try:
        print(INTAKE_TIME)
        patientData = get_patient(request.forms.get("id"))
        # mean = request.forms.get("mean", INTAKE_TIME[0])
        # sigma = request.forms.get("sigma", INTAKE_TIME[1])
        print("intake data: ", patientData)
        mean = INTAKE_TIME[0]
        print("Mean:", mean)
        sigma = INTAKE_TIME[1]
        patientData["total_time"] += np.random.normal(mean, sigma)

        print("Intake Time:", patientData["total_time"])
        return
    except Exception as e:
        print("intake_error: ", e)
        return e


@post("/er_treatment")
def er_treatmentr():
    try:
        patientData = get_patient(request.forms.get("id"))
        mean = request.forms.get("mean", EMERGENCY_TIME[0])
        sigma = request.forms.get("sigma", EMERGENCY_TIME[1])
        patientData["total_time"] += np.random.normal(mean, sigma)
        print("ER Time:", patientData["total_time"])
        return
    except Exception as e:
        print("er_treatment_error: ", e)
        return e


@post("/surgery")
def surgery():
    try:
        patientData = get_patient(request.forms.get("id"))
        mean = SURGERY_TIME[get_patient_type_index(patientData["type"])][0]
        sigma = SURGERY_TIME[get_patient_type_index(patientData["type"])][1]
        patientData["total_time"] += np.random.normal(mean, sigma)
        print("Surgery Time:", patientData["total_time"])
        return
    except Exception as e:
        print("surgery_error: ", e)
        return e


@post("/nursing")
def nursing():
    try:
        patientData = get_patient(request.forms.get("id"))
        mean = NURSING_TIME[get_patient_type_index(patientData["type"])][0]
        sigma = NURSING_TIME[get_patient_type_index(patientData["type"])][1]
        patientData["total_time"] += np.random.normal(mean, sigma)
        print("Nursing Time:", patientData["total_time"])
        return
    except Exception as e:
        print("nursing_error: ", e)
        return e


@post("/releasing")
def releasing():
    try:
        patientData = get_patient(request.forms.get("id"))
        print("Patient Released:", patientData)
        return
    except Exception as e:
        print("releasing_error: ", e)
        return e


# returns index of patient type from the given patient type array (returns 0 for EM-A1 patient since A1 = 0)
def get_patient_type_index(patientType):
    if patientType.startswith("EM") and patientType.split("-")[1].length() > 0:
        patientType = patientType.split("-")[1]
    return PATIENT_TYPES.index(patientType)


# init the database if not alreadt present
def create_database():
    connection = sqlite3.connect("hospital.db")
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL,
            admission_time TEXT NOT NULL,
            diagnosis TEXT,
            resources TEXT,
            scheduled TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            current INTEGER NOT NULL,
            max INTEGER NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


# adds new patient to database and returns id
def add_patient(patientData):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO patients(type, admission_time, diagnosis, resources, scheduled)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                patientData["type"],
                patientData["admission_time"],
                patientData["diagnosis"],
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


# returns patient data from database
def get_patient(patientId):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM patients
            WHERE id = ?
            """,
            (patientId,),
        )
        patientData = cursor.fetchone()
        connection.close()
        return patientData
    except Exception as e:
        print("get_patient_error: ", e)
        return


# updates patient data in database
def set_patient(patientData):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE patients
            SET type = ?, admission_time = ?, diagnosis = ?, resources = ?, scheduled = ?
            WHERE id = ?
            """,
            (
                patientData["type"],
                patientData["admission_time"],
                patientData["diagnosis"],
                patientData["resources"],
                patientData["scheduled"],
                patientData["id"],
            ),
        )
        connection.commit()
        connection.close()
        return
    except Exception as e:
        print("set_patient_error: ", e)
        return


# adds resource to database resource table
def add_resource(resource):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO resources(name, current, max)
            VALUES(?, ?, ?)
            """,
            (
                resource["name"],
                resource["current"],
                resource["max"],
            ),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid
    except Exception as e:
        print("add_resource_error: ", e)
    return


# returns True if patient has complications for the given probability
def check_for_complications(probability):
    return pr.prob(probability)


# creates new process instance
def create_instance(patientData, behavior="fork_running"):
    try:
        if not patientData["type"] or patientData["type"] not in PATIENT_TYPES:
            raise ValueError("Patient Type invalid: " + patientData["type"])
        if behavior not in INSTANCE_TYPES:
            raise ValueError("Instance Type invalid:" + behavior)
        url = "https://cpee.org/flow/start/url/"
        xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
        data = {"behavior": behavior, "url": xml_url, "init": patientData}

        response = requests.post(url, data=data)
        instanceData = {}
        instanceData["instance"] = response.forms.get("CPEE-INSTANCE")
        instanceData["url"] = response.fomrms.get("CPEE-INSTANCE-URL")
        instanceData["id"] = response.forms.get("CPEE-INSTANCE-UUID")
        instanceData["beahvior"] = response.forms.get("CPEE-BEHAVIOR")
        print("Instance Data:", instanceData)
        return response
    except Exception as e:
        print("create_instance_error: ", e)
        return e


# creates tables if tables not there already
create_database()

# add resources to database
for resource in RESOURCES:
    add_resource(resource)

# patient = {"type": "A"}
# response = create_instance(patient)
# print(response.text)

# start the server with tcp6
run(host="::1", port=23453)
