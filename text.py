import bottle
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=1)

@bottle.route('/task', method='GET')
def async_wait():
    callback_url = bottle.request.headers['CPEE-CALLBACK']
    print(f"CallBack-ID: {callback_url}")

    # Start the background task
    executor.submit(background_task, callback_url)

    # Immediate response indicating the request is accepted for async processing
    return bottle.HTTPResponse(
        json.dumps({'Ack.:': 'Response later'}),
        status=202,
        headers={'content-type': 'application/json', 'CPEE-CALLBACK': 'true'}
    )
    

def background_task(callback_url):
    # Sleep for 20 seconds
    time.sleep(20)

    # Perform the background processing here
    print("Background processing completed after 20 seconds")

    # Prepare the callback response as JSON
    callback_response = {
        'task_id': 'task_id',
        'status': 'completed',
        'result': {'success': True}
    }

    # Prepare the headers
    headers = {
        'content-type': 'application/json',
        'CPEE-CALLBACK': 'true'
    }

    # Send the callback response as a JSON payload
    requests.put(callback_url, headers=headers, json=callback_response)
    print(f"PUT request sent to callback_url: {callback_url}")
    
    
bottle.run(host='::0', port=12790)