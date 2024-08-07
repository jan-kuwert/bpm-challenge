#! /usr/bin/python3
import json
import sqlite3
import requests
import numpy as np
from pyprobs import Probability as pr
from bottle import get, request, run, HTTPResponse
from concurrent.futures import ThreadPoolExecutor
import time

EXECUTOR = ThreadPoolExecutor(max_workers=1)

# saves possible behaviors for the cpee instance from config
INSTANCE_BEHAVIORS = ""
# contains: instance (cpee response with ID etc.), entity_id (int), wait (bool), finished (bool)
QUEUE = []
# contains at what time which entity uses what resource
# each resource has its own array in the order of config file
# each array contains entries [resource_name, start_time, end_time, entity_id]
RESOURCE_SCHEDULES = []
# saves the current time of the simulation
CURRENT_TIME = 0.0
PROCESS_NAME = "process"  # default process name, allow to name i.e. db file
# process_entity = the element that is being processed (in the hospital case its a patient)

LIST = [
    "data",  # everything the entity needs to know but the sim doesnt, saved in the db and can be returned if needed in cpee
    "start_time",  # in hours, tracks entity start time in process
    "total_time",  # in hours, tracks total time of entity in process
    "resource",  # the next resource the entity needs
    "resource_available",  # if the resource is available for the entity, "true" or "false
    "priority",  # give entity an int priority for queueing, 0 is default and lowest. 1 highest prio, 2 second highest etc
    "mean",  # mean and standard deviation for the normal distribution to calc time of task
    "sigma",
]


@get("/task")
def handle_task_async():
    try:
        # Get the callback url from the request
        callback_url = request.headers["CPEE-CALLBACK"]
        entity = {}  # entity object to store the process_entity data
        task_type = request.query.get("task_type")
        entity["id"] = request.query.get("id")  # id of the entity in db
        if (entity["id"] is not None) and (entity["id"] != ""):
            entity = get_process_entity(entity["id"])
        for key in LIST:
            key_data = request.query.get(key)
            if key_data is not None and key_data != "":
                entity[key] = key_data
            elif (entity["id"] is None) or (entity["id"] == ""):
                entity[key] = None
        mean = request.query.get("mean")
        sigma = request.query.get("sigma")
        set_process_entity(entity)
        # start the task execution
        EXECUTOR.submit(task, task_type, entity, mean, sigma, callback_url)

        # Immediate response indicating the request is accepted for async processing
        return HTTPResponse(
            json.dumps({"Ack": "Response later"}),
            status=202,
            headers={"content-type": "application/json", "CPEE-CALLBACK": "true"},
        )
    except Exception as e:
        print("exception occured: ", e)
        return e


def task(task_type, entity, mean, sigma, callback_url):
    try:
        global QUEUE, CURRENT_TIME
        wait = True
        # check if instances turn for processing else wait
        print("task: ", task_type, entity["id"])
        if (entity["id"] is not None) and (entity["id"] != ""):
            entity = get_process_entity(entity["id"])
            while wait:
                instance = get_instance(entity["id"])

                if instance is None:
                    print("no waiting needed", CURRENT_TIME, entity["start_time"])
                    break
                if float(entity["start_time"]) <= CURRENT_TIME:
                    wait = False
                    print("wait over")
                else:
                    time.sleep(0.5)
                    print("waiting", entity["id"])

        if task_type == "arrival":
            print("arrival: ", entity)
            # if entity is new init and add it to db
            if (entity["id"] is None) or (entity["id"] == ""):
                entity["resource_available"] = "false"
                entity["id"] = add_process_entity(entity)
                if QUEUE == [] or QUEUE[0]["start_time"] < CURRENT_TIME:
                    print(
                        "time set to "
                        + str(entity["start_time"])
                        + " from "
                        + str(CURRENT_TIME)
                    )
                    CURRENT_TIME = entity["start_time"]
            # if entitiy already exists get it from db
            else:
                set_resource_available(entity, mean, sigma)

        elif task_type == "reschedule":
            entity = get_process_entity(entity["id"])
            new_instance = [
                create_instance(entity),
                entity["id"],
                True,
                False,
            ]
            added = False
            if len(QUEUE) == 0:
                # sends the instance to appending
                added = False
            else:
                for i, instance in enumerate(QUEUE):
                    current_entity = get_process_entity(instance[1])
                    if (
                        current_entity["start_time"] + current_entity["total_time"]
                        < CURRENT_TIME
                    ):
                        QUEUE = (
                            QUEUE[:i]
                            + [new_instance, entity["id"], False, False]
                            + QUEUE[i:]
                        )
                        entity["start_time"] = CURRENT_TIME + 24.0
                        set_process_entity(entity)
                        added = True
                        break
            if not added:
                QUEUE.append(new_instance)
                entity["start_time"] = CURRENT_TIME + 24.0
                set_process_entity(entity)
        elif task_type == "resource":
            if (entity["id"] is not None) or (entity["id"] != ""):
                entity = get_process_entity(entity["id"])
                print("resource: ", entity)
                resource = get_resource(entity["resource"])
                task_time = np.random.normal(mean, sigma)
                RESOURCE_SCHEDULES[resource["id"]].append(
                    [CURRENT_TIME, CURRENT_TIME + task_time, entity["id"]]
                )
                print(RESOURCE_SCHEDULES[resource["id"]])
                entity["resource_available"] = "true"
                entity["total_time"] = float(entity["total_time"]) + task_time
                set_process_entity(entity)
            else:
                entity["resource_available"] = "false"
        elif task_type == "finish":
            instance = get_instance(entity["id"])
            print(1, instance)
            instance[3] = True  # set finished to true
            print(2)
            set_instance(instance)
            print(3)
            CURRENT_TIME += 24
            print(4)
            entity = get_process_entity(entity["id"])
            print(5)
            print("finished: ", entity, CURRENT_TIME),
        callback(callback_url, entity)
    except Exception as e:
        print(task + "_error: ", entity["id"], e)
        return e


def set_resource_available(entity, mean, sigma):
    try:
        entity = get_process_entity(entity["id"])
        resource = get_resource(entity["resource"])
        schedule = RESOURCE_SCHEDULES[resource["name"]]
        # calculate duration of task
        duration = np.random.normal(mean, sigma)
        # saves all entries that are using the current resource at the time the entitie wants to use it too
        relevant_entries = []
        for entry in schedule:
            # check end time of entry and start time of current entity
            if entry[1] >= entity["start_time"] and entry[2] < entity["start_time"]:
                relevant_entries.append(entry)
            if len(relevant_entries) == resource["max"]:
                # if whole resource already in use, sort by end time and take the earliest end time for the new start time
                relevant_entries.sort(key=lambda x: x[2])
                # add the waiting time to the total time of the entity until resource is free
                entity["total_time"] = (
                    entity["total_time"] + entity["start_time"] - relevant_entries[0][2]
                )
                entity["start_time"] = relevant_entries[0][2]

        entity["total_time"] = entity["total_time"] + duration

        if len(relevant_entries) < resource["max"]:
            entity["resource_available"] = "true"
            set_process_entity(entity)
            RESOURCE_SCHEDULES[resource["name"]].append(
                [
                    resource["name"],
                    entity["start_time"],
                    entity["start_time"] + duration,
                    entity["id"],
                ]
            )
        else:
            entity["resource_available"] = "false"
    except Exception as e:
        print("set_resource_available_error: ", e)
        return e


def get_instance(entity_id):
    try:
        for instance in QUEUE:
            if instance[1] == entity_id:
                return instance
        return None
    except Exception as e:
        print("get_instance_error: ", e)


def set_instance(updated_instance):
    try:
        for instance in QUEUE:
            if instance[1] == updated_instance[1]:
                instance = updated_instance
    except Exception as e:
        print("set_instance_error: ", e)


def callback(callback_url, entity):
    try:
        # Prepare the headers
        headers = {"content-type": "application/json", "CPEE-CALLBACK": "true"}

        # Send the callback response
        requests.put(callback_url, headers=headers, json=entity)
    except Exception as e:
        print("callback_error: ", e)
        return e


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
            resource_available TEXT,
            priority INTEGER DEFAULT 0
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            max TEXT NOT NULL,
            schedule TEXT
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
            INSERT INTO process_entities(data, start_time, total_time, resource, resource_available)
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
            (int(entity_id),),
        )
        entity = cursor.fetchone()
        connection.close()
        response = {
            "id": entity[0],
            "data": entity[1],
            "start_time": entity[2],
            "total_time": entity[3],
            "resource": entity[4],
            "resource_available": entity[5],
        }
        return response
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
def add_resource(resource_name, resource_max, resource_schedule):
    try:
        connection = sqlite3.connect(PROCESS_NAME + ".db")
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO resources(name, max, schedule)
            VALUES(?, ?, ?)
            """,
            (
                resource_name,
                resource_max,
                resource_schedule,
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
        response = {
            "id": resource[0],
            "name": resource[1],
            "max": resource[2],
            "schedule": resource[3],
        }
        print("get_resource: ", response)
        return response
    except Exception as e:
        print("get_resource_error: ", e)
        return


# update resource in the db
def set_resource(resource_data):
    try:
        connection = sqlite3.connect("hospital.db")
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE resources
            SET name = ?, max = ?, schedule = ?
            WHERE id = ?
            """,
            (
                resource_data["name"],
                resource_data["max"],
                resource_data["schedule"],
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
def create_instance(entity, behavior="fork_running"):
    try:
        if behavior not in INSTANCE_BEHAVIORS:
            raise ValueError("Instance Behavior invalid:" + behavior)
        if entity["id"] is None:
            raise ValueError("Entity id is None")
        url = "https://cpee.org/flow/start/url/"
        xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
        data = {
            "behavior": behavior,
            "url": xml_url,
            "init": '{"id": "'
            + str(entity["id"])
            + '", "type": "'
            + str(entity["data"].split(",")[0])
            + '", "diagnosis": "'
            + str(entity["data"].split(",")[1])
            + '"}',
        }

        response = requests.post(url, data=data)
        # response.text:  {'CPEE-INSTANCE': '49212', 'CPEE-INSTANCE-URL': 'https://cpee.org/flow/engine/49212', 'CPEE-INSTANCE-UUID': '821faad9-e39f-4a0e-871b-2f217920562c', 'CPEE-BEHAVIOR': 'fork_running'}
        return response.text
    except Exception as e:
        print("create_instance_error: ", e)
        return e


def __init__():
    global INSTANCE_BEHAVIORS, PROCESS_NAME, RESOURCE_SCHEDULES
    file = open("config.json")
    config = json.load(file)
    INSTANCE_BEHAVIORS = config["instance_behaviors"]
    PROCESS_NAME = config["process_name"]
    create_database()
    # add resources to db
    for resource in config["resources"]:
        add_resource(resource["name"], resource["max"], "[]")
        RESOURCE_SCHEDULES.append([resource["name"]])
    file.close()


__init__()

run(host="::1", port=23453)
