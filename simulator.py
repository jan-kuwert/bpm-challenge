#! /usr/bin/python3
import requests
import json
from bottle import  route, run, template, post, get, put, delete

@get('/names/<name>')
def index(name):
    return template('<b>Hello {name} </>!', name=name)

def new_instance(behavior='fork_running', type='A'):
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
