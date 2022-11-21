#!/usr/bin/python3
import os, sys
import docker
import threading, time
from flask import Flask, render_template

client = docker.from_env()
APIClient = docker.APIClient(base_url='unix://var/run/docker.sock')

def status():
    res = {}
    tasks = APIClient.tasks()
    for task in tasks:
        spec = task['Spec']
        status = task['Status']
        NodeID = task['NodeID']
        image = spec['ContainerSpec']['Image'].split('@')[0]
        state, message = status['State'], status['Message']
        node_name = client.nodes.get(NodeID).attrs['Description']['Hostname']
        # print(node_name, image, state, message)
        res.setdefault(node_name, []).append((image, state, message))
    for k in res:
        res[k].sort(key=lambda x: x[0])
    return res


app = Flask(
    __name__,
    template_folder='templates',
)

@app.get('/')
def page():
    return render_template('index.html', status=status())

@app.get('/ping')
def ping():
    return 'pong', 200

if __name__ == '__main__':
    app.run(
	    host='0.0.0.0',
	    debug=False,
	    port=8888
    )