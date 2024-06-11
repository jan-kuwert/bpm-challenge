#! /usr/bin/python3
import requests
from enum import Enum, auto
from bottle import  route, run, template, post, get, put, delete

class InstanceType(Enum):
    fork_running = auto()
    fork_ready = auto()
    wait_running = auto()
    wait_ready = auto()

@get('/names/<name>')
def index(name):
    return template('<b>Hello {name} </>!', name=name)

@get('/intake')
def index():

    return 


def new_instance(behavior:InstanceType='fork_running', type='A'):
    url = "https://cpee.org/flow/start/url/"
    xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
    data = {
        "behavior": behavior,
        "url": xml_url,
        "init": {"type": type}
    }
    
    response = requests.post(url, data=data)
    # json_response = response.read()
    # json_response = json.loads(response)
    #instance = json_response['CPEE_INSTANCE']
    print("Respone:", response.response)

new_instance()

run(host='::1', port=23453)
