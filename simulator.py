#! /usr/bin/python3
import json
import sqlite3
import requests
import numpy as np
from pyprobs import Probability as pr
from bottle import get, request, run, HTTPResponse
from concurrent.futures import ThreadPoolExecutor
import time

INSTANCE_BEHAVIORS = ["fork_running", "fork_ready", "wait_running", "wait_ready"]

EXECUTOR = ThreadPoolExecutor(max_workers=1)
INSTANCES = []
QUEUE = []
CURRENT_TIME = 0
PROCESS_NAME = "process"  # default process name, allow to name i.e. db file
# process_entity = the element that is being processed (in the hospital case its a patient)


@get("/task")
def handle_task_async():
    try:
        # Get the callback url from the request
        callback_url = request.headers["CPEE-CALLBACK"]
        entity = {}  # entity object to store the process_entity data
        entity["id"] = request.query.get("id")  # id of the entity in db
        entity["data"] = request.query.get(
            "data"
        )  # everything the entity needs to know but the sim doesnt
        entity["start_time"] = request.query.get(
            "start_time"
        )  # in hours, tracks entity start time in process
        entity["total_time"] = request.query.get(
            "total_time"
        )  # in hours, tracks total time of entity in process
        entity["resource"] = request.query.get(
            "resource", ""
        )  # the next resource the entity needs
        # mean and standard deviation for the normal distribution to calc time of task
        mean = request.query.get("mean", 0)
        sigma = request.query.get("sigma", 0)
        print("data: ", entity)
        # start the task execution
        EXECUTOR.submit(task, entity, mean, sigma, callback_url)

        # Immediate response indicating the request is accepted for async processing
        return HTTPResponse(
            json.dumps({"Ack": "Response later"}),
            status=202,
            headers={"content-type": "application/json", "CPEE-CALLBACK": "true"},
        )
    except Exception as e:
        print("exception occured: ", e)
        return e


def task(entity, mean, sigma, callback_url):
    try:
        # check if new entity
        if (entity["id"] is None) or (entity["id"] == ""):
            entity["id"] = add_process_entity(entity)
            entity["resource"] = ""
            entity["resource_available"] = "false"
            set_process_entity(entity)
        # if entitiy already exists get it from db
        else:
            entity = get_process_entity(entity["id"])

            if entity["resource"] != "":
                resource = get_resource(entity["resource"])
                if resource["current"] < resource["max"]:
                    resource["current"] += 1
                    set_resource(resource)
                    entity["resource_available"] = "true"
                else:
                    entity["resource_available"] = "false"
            # if no resource replan
            elif entity["resource_available"] == "false" and entity["resource"] == "":
                create_instance(entity["id"], entity["data"])
            entity["total_time"] += np.random.normal(mean, sigma)
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


# creates database if not existing already
def create_database():
    connection = sqlite3.connect(PROCESS_NAME + ".db")
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS process_entities(
            id INTEGER PRIMARY KEY,
            data TEXT,
            start_time REAL NOT NULL,
            total_time REAL,
            resource TEXT, 
            resource_available TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
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


# adds new patient to database and returns id
def add_process_entity(entity):
    try:
        connection = sqlite3.connect(PROCESS_NAME + ".db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO process_entities(data, start_time, total_time, reource, resource_available)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                entity["data"],
                entity["start_time"],
                entity["total_time"],
                entity["resource"],
                entity["resource_available"],
            ),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid
    except Exception as e:
        print("add_process_entity_error: ", e)
    return


# returns patient data from database
def get_process_entity(entity_id):
    try:
        connection = sqlite3.connect(PROCESS_NAME + ".db")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT * FROM process_entities
            WHERE id = ?
            """,
            (entity_id,),
        )
        entity = cursor.fetchone()
        connection.close()
        return entity
    except Exception as e:
        print("get_process_entity_error: ", e)
        return


# updates patient data in database
def set_process_entity(entity):
    try:
        connection = sqlite3.connect(PROCESS_NAME + ".db")
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE process_entities
            SET data = ? , start_time =?, total_time = ?, resource = ?, resource_available = ?
            WHERE id = ?
            """,
            (
                entity["data"],
                entity["start_time"],
                entity["total_time"],
                entity["resource"],
                entity["resource_available"],
                entity["id"],
            ),
        )
        connection.commit()
        connection.close()
        return
    except Exception as e:
        print("set_process_entity_error: ", e)
        return


# adds resource to database resource table
def add_resource(resource_name, resource_data):
    try:
        connection = sqlite3.connect(PROCESS_NAME + ".db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO resources(name, data)
            VALUES(?,?)
            """,
            (
                resource_name,
                resource_data,
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
        connection = sqlite3.connect(PROCESS_NAME + ".db")
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
        return resource
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


# creates new process instance with object id and if needed additional data
def create_instance(object_id, object_data={}, behavior="fork_running"):
    try:
        if behavior not in INSTANCE_BEHAVIORS:
            raise ValueError("Instance Behavior invalid:" + behavior)

        url = "https://cpee.org/flow/start/url/"
        xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
        data = {
            "behavior": behavior,
            "url": xml_url,
            "init": '{"id": "'
            + str(object_id)
            + ","
            + str(object_data).replace("{", "").replace("}", "")
            + '"}',
        }

        response = requests.post(url, data=data)
        return (
            response.text
        )  # response:  {'CPEE-INSTANCE': '49212', 'CPEE-INSTANCE-URL': 'https://cpee.org/flow/engine/49212', 'CPEE-INSTANCE-UUID': '821faad9-e39f-4a0e-871b-2f217920562c', 'CPEE-BEHAVIOR': 'fork_running'}
    except Exception as e:
        print("create_instance_error: ", e)
        return e


def __init__():
    file = open("config.json")
    config = json.load(file)

    PROCESS_NAME = config["process_name"]
    create_database()

    # add resources to db
    for resource in config["resources"]:
        add_resource(resource.pop("name"), str(resource))
    file.close()


__init__()

run(host="::1", port=23453)
