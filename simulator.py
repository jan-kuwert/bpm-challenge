#! /usr/bin/python3
import json
import sqlite3
import requests
import numpy as np
from enum import Enum, auto
from pyprobs import Probability as pr
from bottle import run, request, post

# for now in here
resources = [
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
        patient_data = {}
        patient_data["id"] = request.forms.get("id")
        if not patient_data["id"]:
            patient_data["type"] = request.forms.get("type")
            patient_data["admission_time"] = request.forms.get("admission_time")
            if not patient_data["admission_time"]:
                patient_data["admission_time"] = CURRENT_TIME
            patient_data["start_time"] = CURRENT_TIME
            patient_data["total_time"] = 0  # tracks time spent in hospital
            patient_data["diagnosis"] = request.forms.get("diagnosis")
            if not patient_data["diagnosis"]:
                tuple = patient_data["type"].replace(" ", "").split("-")
                patient_data["type"] = tuple[0]
                patient_data["diagnosis"] = tuple[1]
            patient_data["replanned"] = "false"
            patient_data["resource_available"] = "false"
            patient_data["complications"] = "false"
            patient_data["phantom_pain"] = "false"
            patient_data["id"] = add_patient(patient_data)
        else:
            patient_data = get_patient(patient_data["id"])

        if patient_data["type"] == "EM" or patient_data["replanned"] == "true":
            if patient_data["type"] == "EM":
                patient_data["resource"] = "em"
            else:
                patient_data["resource"] = "intake"

            resource = get_resource(patient_data["resource"])
            if resource["current"] <= 0:
                patient_data["resource_available"] = "false"
            else:
                resource["current"] -= 1
                patient_data["resource_available"] = "true"
                patient_data["resource"] = ""

                set_resource(resource)
                set_patient(patient_data)
        print("patient_admission: ", patient_data)
        set_log(patient_data, "patient_admission")
        return patient_data
    except Exception as e:
        set_log(patient_data, "patient_admission_error", e)
        print("patient_admission_error: ", e)
        return e


@post("/replan_patient")
def replan_patient():
    try:
        patient_data = get_patient(request.forms.get("id"))
        patient_data["replanned"] = "true"
        patient_data["start_time"] = (
            CURRENT_TIME + 12 * 60
        )  # TODO add smart time decision here
        set_patient(patient_data)

        response = create_instance(patient_data)
        set_log(patient_data, "replan_patient")
        return response
    except Exception as e:
        set_log(patient_data, "replan_patient_error", e)
        print("replan_patient_error: ", e)
        return e


@post("/intake")
def intake():
    try:
        resource = get_resource("intake")
        if resource["current"] <= 0:
            raise ValueError("No intake resource available")
        patient_data = get_patient(request.forms.get("id"))
        mean = request.forms.get("mean", INTAKE_TIME[0])
        sigma = request.forms.get("sigma", INTAKE_TIME[1])
        patient_data["total_time"] += np.random.normal(mean, sigma)
        resource["current"] += 1

        set_patient(patient_data)
        set_resource(resource)
        set_log(patient_data, "intake")
        return
    except Exception as e:
        set_log(patient_data, "intake_error", e)
        print("intake_error: ", e)
        return e


@post("/er_treatment")
def er_treatmentr():
    try:
        resource = get_resource("em")
        if resource["current"] <= 0:
            raise ValueError("No em resource available")
        patient_data = get_patient(request.forms.get("id"))
        mean = request.forms.get("mean", EMERGENCY_TIME[0])
        sigma = request.forms.get("sigma", EMERGENCY_TIME[1])
        patient_data["total_time"] += np.random.normal(mean, sigma)
        patient_data["phantom_pain"] = evaluate_probability(PHANTOM_PAIN_PROBABILITY)
        resource["current"] += 1

        set_patient(patient_data)
        set_resource(resource)
        set_log(patient_data, "er_treatment")
        return patient_data
    except Exception as e:
        set_log(patient_data, "er_treatment_error", e)
        print("er_treatment_error: ", e)
        return e


@post("/surgery")
def surgery():
    try:
        resource = get_resource("surgery")
        if resource["current"] <= 0:
            raise ValueError("No surgery resource available")
        patient_data = get_patient(request.forms.get("id"))
        print("surgery: ", patient_data["diagnosis"])
        mean = SURGERY_TIME[get_diagnosis_type_index(patient_data["diagnosis"])][0]
        sigma = SURGERY_TIME[get_diagnosis_type_index(patient_data["diagnosis"])][1]
        patient_data["total_time"] += np.random.normal(mean, sigma)
        resource["current"] += 1

        set_patient(patient_data)
        set_resource(resource)
        set_log(patient_data, "surgery")
        return
    except Exception as e:
        set_log(patient_data, "surgery_error", e)
        print("surgery_error: ", e)
        return e


@post("/nursing")
def nursing():
    try:
        patient_data = get_patient(request.forms.get("id"))
        if "A" in patient_data["diagnosis"]:
            resource = get_resource("nursing_a")
        elif "B" in patient_data["diagnosis"]:
            resource = get_resource("nursing_b")
        if resource["current"] <= 0:
            raise ValueError("No nursing resource available")
        mean = NURSING_TIME[get_diagnosis_type_index(patient_data["diagnosis"])][0]
        sigma = NURSING_TIME[get_diagnosis_type_index(patient_data["diagnosis"])][1]
        patient_data["total_time"] += np.random.normal(mean, sigma)
        patient_data["complications"] = evaluate_probability(
            COMPLICATION_PROBABILITY[
                get_diagnosis_type_index(patient_data["diagnosis"])
            ]
        )
        resource["current"] += 1

        set_patient(patient_data)
        set_resource(resource)
        set_log(patient_data, "nursing")
        return
    except Exception as e:
        set_log(patient_data, "nursing_error", e)
        print("nursing_error: ", e)
        return e


@post("/releasing")
def releasing():
    try:
        patient_data = get_patient(request.forms.get("id"))

        set_log(patient_data, "releasing")
        write_log_to_txt(patient_data["id"])
        return
    except Exception as e:
        set_log(patient_data, "releasing_error", e)
        print("releasing_error: ", e)
        return e


# returns index of patient type from the given patient type array (returns 0 for EM-A1 patient since A1 = 0)
def get_diagnosis_type_index(diagnosis):
    return DIAGNOSIS_TYPES.index(diagnosis)


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
            start_time REAL NOT NULL,
            total_time REAL NOT NULL,
            diagnosis TEXT,
            replanned TEXT,
            resource_available TEXT,
            complications TEXT,
            phantom_pain TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resource(
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
            patient_id INTEGER NOT NULL,
            patient_data TEXT NOT NULL,
            tasks TEXT NOT NULL,
            error TEXT
        )
        """
    )

    connection.commit()
    connection.close()


# adds new patient to database and returns id
def add_patient(patient_data):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO patients(type, admission_time, start_time, total_time, diagnosis, replanned, resource_available, complications, phantom_pain)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_data["type"],
                patient_data["admission_time"],
                patient_data["start_time"],
                patient_data["total_time"],
                patient_data["diagnosis"],
                patient_data["replanned"],
                patient_data["resource_available"],
                patient_data["complications"],
                patient_data["phantom_pain"],
            ),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid
    except Exception as e:
        print("add_patient_error: ", e)
    return


# returns patient data from database
def get_patient(patient_id):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM patients
            WHERE id = ?
            """,
            (patient_id,),
        )
        patient = cursor.fetchone()
        connection.close()
        patient_data = {}
        patient_data["id"] = patient[0]
        patient_data["type"] = patient[1]
        patient_data["admission_time"] = patient[2]
        patient_data["start_time"] = patient[3]
        patient_data["total_time"] = patient[4]
        patient_data["diagnosis"] = patient[5]
        patient_data["replanned"] = patient[6]
        patient_data["resource_available"] = patient[7]
        patient_data["complications"] = patient[8]
        patient_data["phantom_pain"] = patient[9]
        return patient_data
    except Exception as e:
        print("get_patient_error: ", e)
        return


# updates patient data in database
def set_patient(patient_data):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE patients
            SET type = ?, admission_time = ?, start_time =?, total_time =?, diagnosis = ?, replanned = ?, resource_available = ?, complications = ?, phantom_pain = ?
            WHERE id = ?
            """,
            (
                patient_data["type"],
                patient_data["admission_time"],
                patient_data["start_time"],
                patient_data["total_time"],
                patient_data["diagnosis"],
                patient_data["replanned"],
                patient_data["resource_available"],
                patient_data["complications"],
                patient_data["phantom_pain"],
                patient_data["id"],
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
            INSERT OR REPLACE INTO resource(name, current, max)
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
            SELECT * FROM resource
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
def set_resource(resource_data):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        if resource_data["current"] <= resource_data["max"]:
            cursor.execute(
                """
                UPDATE resource
                SET name = ?, current = ?, max = ?
                WHERE id = ?
                """,
                (
                    resource_data["name"],
                    resource_data["current"],
                    resource_data["max"],
                    resource_data["id"],
                ),
            )
        connection.commit()
        connection.close()
        return
    except Exception as e:
        print("set_resource_error: ", e)
        return


def set_log(patient_data, task, error=""):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO logs(patient_id, patient_data, tasks, error)
            VALUES(?, ?, ?, ?)
            """,
            (patient_data["id"], str(patient_data), task, str(error)),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid
    except Exception as e:
        print("set_log_error: ", e)
    return


def get_log(patient_id):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        if patient_id:
            cursor.execute(
                """
                SELECT * FROM logs
                WHERE patient_id = ?
                """,
                (patient_id,),
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


# write whole log or log of a single patient to a txt file
def write_log_to_txt(patient_id=None):
    try:
        log = str(get_log(patient_id))
        with open(f"log-{patient_id}.txt", "w") as file:
            file.write(log)
    except Exception as e:
        print("write_log_to_txt_error: ", e)
        return


# returns True if patient has complications for the given probability
def evaluate_probability(probability):
    return pr.prob(probability)


# creates new process instance
def create_instance(patient_data, behavior="fork_running"):
    try:
        if not patient_data["type"] or patient_data["type"] not in PATIENT_TYPES:
            raise ValueError("Patient Type invalid: " + patient_data["type"])
        if behavior not in INSTANCE_TYPES:
            raise ValueError("Instance Type invalid:" + behavior)
        url = "https://cpee.org/flow/start/url/"
        xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
        data = {
            "behavior": behavior,
            "url": xml_url,
            "init": '{"type": "'
            + patient_data["type"]
            + '", "diagnosis": "'
            + patient_data["diagnosis"]
            + '"}',
        }

        response = requests.post(url, data=data)
        return response
    except Exception as e:
        print("create_instance_error: ", e)
        return e


# creates tables if tables not there already
create_database()

# add resource to database
for resource in resources:
    add_resource(resource)

# start the server with tcp6
run(host="::1", port=23453)
