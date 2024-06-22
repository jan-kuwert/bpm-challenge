import json
import sqlite3
import requests
import numpy as np
from pyprobs import Probability as pr
from bottle import get, request, run, HTTPResponse
from concurrent.futures import ThreadPoolExecutor
import time

INSTANCE_TYPES = ["fork_running", "fork_ready", "wait_running", "wait_ready"]

executor = ThreadPoolExecutor(max_workers=1)


@get("/task")
def handle_task_async():
    try:
        # Get the callback url from the request
        callback_url = request.headers["CPEE-CALLBACK"]
        data = request.query.allitmes()
        print("data: ", data)
        # start the task execution
        executor.submit(task, data, callback_url)

        # Immediate response indicating the request is accepted for async processing
        return HTTPResponse(
            json.dumps({"Ack.:": "Response later"}),
            status=202,
            headers={"content-type": "application/json", "CPEE-CALLBACK": "true"},
        )
    except Exception as e:
        print("exception occured: ", e)
        return e


def task(data, callback_url):
    try:
        print("task started")
    except Exception as e:
        print("task_error: ", e)
    callback(callback_url)


def callback(callback_url):
    callback_response = {
        "task_id": "task_id",
        "status": "completed",
        "result": {"success": True},
    }

    # Prepare the headers
    headers = {"content-type": "application/json", "CPEE-CALLBACK": "true"}

    # Send the callback response
    requests.put(callback_url, headers=headers, json=callback_response)


def create_database():
    connection = sqlite3.connect("hospital.db")
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS task_objects(
            id INTEGER PRIMARY KEY,
            data TEXT,
            start_time REAL NOT NULL,
            total_time REAL NOT NULL,
            resource_available TEXT,
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources(
            id INTEGER PRIMARY KEY,
            data TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY,
            task_object_id
            tasks TEXT NOT NULL,
            error TEXT
        )
        """
    )

    connection.commit()
    connection.close()


# creates new process instance
def create_instance(patient_data, behavior="fork_running"):
    try:
        if not patient_data["type"]:
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
            + '", "id": "'
            + str(patient_data["id"])
            + '"}',
        }

        response = requests.post(url, data=data)
        return response
    except Exception as e:
        print("create_instance_error: ", e)
        return e


run(host="::1", port=23453)
