#!/usr/bin/python3.8
import os
import subprocess
try:
    from dotenv import load_dotenv
except:
    print("Please install python-dotenv")
    print("python3.8 -m pip install python-dotenv")
    exit(1)

DOCKER_MANAGER = ''
DOCKER_HOSTS = []

def read_env():
    global DOCKER_MANAGER
    global DOCKER_HOSTS
    load_dotenv()
    DOCKER_MANAGER = os.getenv("MASTER_HOST")
    DOCKER_HOSTS = os.getenv("CASSANDRA_CLUSTER").split(",")
    print(f"DOCKER_MANAGER: {DOCKER_MANAGER}")
    print(f"DOCKER_HOSTS: {DOCKER_HOSTS}")
    try:
        DOCKER_HOSTS.remove(DOCKER_MANAGER)
    except ValueError:
        pass    

def print_help():
    help_str = """commands:
    help: print this help
    exit: exit the program
    env: realod the .env file
    cassandra: start cassandra cluster
    swarm: make a docker swarm
    deploy: deploy the stack
    run: cassandra + swarm + deploy
    stop: stop the stack and the cassandra cluster
    """
    print(help_str)

def cassandra_cluster():
    subprocess.run(["./startCluster", DOCKER_MANAGER, *DOCKER_HOSTS])

def docker_swarm():
    subprocess.run(["./makeSwarm.py", DOCKER_MANAGER, *DOCKER_HOSTS])

def docker_stack_deploy():
    subprocess.run(["docker", "stack", "deploy", "-c", "docker-compose.yml", "a2"])

def stop_cassandra_cluster():
    subprocess.run(["./stopCluster", DOCKER_MANAGER, *DOCKER_HOSTS])

def remove_stack():
    subprocess.run(["docker", "stack", "rm", "a2"])

def read_command():
    while True:
        print("> ", end="")
        command = input()
        if command == "exit":
            break
        if command == "help":
            print_help()
        if command == "env":
            read_env()
        if command == "cassandra":
            cassandra_cluster()
        if command == "swarm":
            docker_swarm()
        if command == "deploy":
            docker_stack_deploy()
        if command == "run":
            cassandra_cluster()
            docker_swarm()
            docker_stack_deploy()
        if command == "stop":
            remove_stack()
            stop_cassandra_cluster()


if __name__ == "__main__":
    read_env()
    read_command()