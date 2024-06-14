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
    [False],
    [1, 0.25],
    [2, 0.5],
    [4, 0.5],
    [False],
    [False],
    [4, 0.5],
    [4, 1],
]
NURSING_TIME = [[4, 0.5], [8, 2], [16, 2], [16, 2], [8, 2], [16, 2], [16, 4], [16, 4]]
EMERGENCY_TIME = [2, 0.5]
COMPLICATION_PROBABILITY = [0.01, 0.01, 0.02, 0.02, 0.001, 0.001, 0.002, 0.002]
PHANTOM_PAIN_PROBABILITY = 0.01


@post("/patient_admission")
def patient_admission():
    try:
        patientData = {}
        patientData["id"] = request.forms.get("id")
        if not patientData["id"]:
            patientData["type"] = request.forms.get("type")
            patientData["admission_time"] = request.forms.get("admission_time")
            if not patientData["admission_time"]:
                patientData["admission_time"] = datetime.now().strftime(
                    "%m/%d/%Y, %H:%M:%S"
                )
            patientData["start_time"] = CURRENT_TIME
            patientData["total_time"] = 0  # tracks time spent in hospital
            patientData["diagnosis"] = request.forms.get("diagnosis")
            patientData["scheduled"] = "false"
            patientData["resources"] = request.forms.get("resources")
            if patientData["resources"] == None and patientData["type"] != "EM":
                patientData["resources"] = "intake"
            elif patientData["type"] == "EM":
                patientData["resources"] = "EM"
            patientData["resources_available"] = True  # TODO implement
            patientData["complications"] = False
            patientData["phantom_pain"] = False
            patientData["id"] = add_patient(patientData)
        else:
            patientData = get_patient(patientData["id"])

        set_log(patientData, "patient_admission")
        return patientData
    except Exception as e:
        set_log(patientData, "patient_admission_error", e)
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
        set_log(patientData, "replan_patient")
        return response
    except Exception as e:
        set_log(patientData, "replan_patient_error", e)
        print("replan_patient_error: ", e)
        return e


@post("/intake")
def intake():
    try:
        patientData = get_patient(request.forms.get("id"))
        print(patientData)
        mean = request.forms.get("mean", INTAKE_TIME[0])
        sigma = request.forms.get("sigma", INTAKE_TIME[1])
        patientData["total_time"] = str(
            float(patientData["total_time"]) + np.random.normal(mean, sigma)
        )
        set_log(patientData, "intake")
        return
    except Exception as e:
        set_log(patientData, "intake_error", e)
        print("intake_error: ", e)
        return e


@post("/er_treatment")
def er_treatmentr():
    try:
        patientData = get_patient(request.forms.get("id"))
        mean = request.forms.get("mean", EMERGENCY_TIME[0])
        sigma = request.forms.get("sigma", EMERGENCY_TIME[1])
        patientData["total_time"] += np.random.normal(mean, sigma)
        patientData["phantom_pain"] = evaluate_probability(PHANTOM_PAIN_PROBABILITY)
        set_log(patientData, "er_treatment")
        return patientData
    except Exception as e:
        set_log(patientData, "er_treatment_error", e)
        print("er_treatment_error: ", e)
        return e


@post("/surgery")
def surgery():
    try:
        patientData = get_patient(request.forms.get("id"))
        mean = SURGERY_TIME[get_patient_type_index(patientData["type"])][0]
        sigma = SURGERY_TIME[get_patient_type_index(patientData["type"])][1]
        patientData["total_time"] += np.random.normal(mean, sigma)
        set_log(patientData, "surgery")
        return
    except Exception as e:
        set_log(patientData, "surgery_error", e)
        print("surgery_error: ", e)
        return e


@post("/nursing")
def nursing():
    try:
        patientData = get_patient(request.forms.get("id"))
        mean = NURSING_TIME[get_patient_type_index(patientData["type"])][0]
        sigma = NURSING_TIME[get_patient_type_index(patientData["type"])][1]
        patientData["total_time"] += np.random.normal(mean, sigma)
        patientData["complications"] = evaluate_probability(
            COMPLICATION_PROBABILITY[get_patient_type_index(patientData["type"])]
        )
        set_log(patientData, "nursing")
        return
    except Exception as e:
        set_log(patientData, "nursing_error", e)
        print("nursing_error: ", e)
        return e


@post("/releasing")
def releasing():
    try:
        patientData = get_patient(request.forms.get("id"))
        set_log(patientData, "releasing")
        write_log_to_txt(patientData["id"])
        return
    except Exception as e:
        set_log(patientData, "releasing_error", e)
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
            start_time TEXT NOT NULL,
            total_time TEXT NOT NULL,
            diagnosis TEXT,
            scheduled TEXT,
            resources TEXT,
            resources_available TEXT,
            complications TEXT,
            phantom_pain TEXT
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY,
            patientId INTEGER NOT NULL,
            patientData TEXT NOT NULL,
            tasks TEXT NOT NULL,
            error TEXT
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
            INSERT INTO patients(type, admission_time, start_time, total_time, diagnosis, scheduled, resources, resources_available, complications, phantom_pain)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patientData["type"],
                patientData["admission_time"],
                patientData["start_time"],
                patientData["total_time"],
                patientData["diagnosis"],
                patientData["scheduled"],
                patientData["resources"],
                patientData["resources_available"],
                patientData["complications"],
                patientData["phantom_pain"],
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
        patient = cursor.fetchone()
        connection.close()
        patientData = {}
        patientData["id"] = patient[0]
        patientData["type"] = patient[1]
        patientData["admission_time"] = patient[2]
        patientData["start_time"] = patient[3]
        patientData["total_time"] = patient[4]
        patientData["diagnosis"] = patient[5]
        patientData["scheduled"] = patient[6]
        patientData["resources"] = patient[7]
        patientData["resources_available"] = patient[8]
        patientData["complications"] = patient[9]
        patientData["phantom_pain"] = patient[10]
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
            SET type = ?, admission_time = ?, start_time =?, total_time =?, diagnosis = ?, scheduled = ?, resources = ?, resources_available = ?, complications = ?, phantom_pain = ?
            WHERE id = ?
            """,
            (
                patientData["type"],
                patientData["admission_time"],
                patientData["start_time"],
                patientData["total_time"],
                patientData["diagnosis"],
                patientData["scheduled"],
                patientData["resources"],
                patientData["resources_available"],
                patientData["complications"],
                patientData["phantom_pain"],
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


# returns resource from the database
def get_resource(resource_name):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM resources
            WHERE name = ?
            """,
            (resource_name,),
        )
        resource = cursor.fetchone()
        connection.close()
        resourceData = {}
        resourceData["id"] = resource[0]
        resourceData["name"] = resource[1]
        resourceData["current"] = resource[2]
        resourceData["max"] = resource[3]
        return resourceData
    except Exception as e:
        print("get_resource_error: ", e)
        return


# update resource in the db
def set_resource(resourceData):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE resources
            SET name = ?, current = ?, max = ?
            WHERE id = ?
            """,
            (
                resourceData["name"],
                resourceData["current"],
                resourceData["max"],
                resourceData["id"],
            ),
        )
        connection.commit()
        connection.close()
        return
    except Exception as e:
        print("set_resource_error: ", e)
        return


def set_log(patientData, task, error=''):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO logs(patientId, patientData, tasks, error)
            VALUES(?, ?, ?, ?)
            """,
            (patientData["id"], patientData, task, error),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid
    except Exception as e:
        print("set_log_error: ", e)
    return


def get_log(patientId):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        if patientId:
            cursor.execute(
                """
                SELECT * FROM logs
                WHERE patientId = ?
                """,
                (patientId,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM logs
                """
            )
        logs = cursor.fetchall()
        connection.close()
        return logs
    except Exception as e:
        print("get_log_error: ", e)
        return


def write_log_to_txt(patientId=None):
    try:
        log = get_log(patientId)
        with open(f"log-{patientId}.txt", "a") as file:
            file.write(log)
    except Exception as e:
        print("write_log_to_txt_error: ", e)
        return


# returns True if patient has complications for the given probability
def evaluate_probability(probability):
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
