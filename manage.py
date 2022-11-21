#!/usr/bin/python3.8
import os
import subprocess
try:
    from dotenv import load_dotenv
except:
    print("Please install python-dotenv")
    print("python3.8 -m pip install python-dotenv")
    exit(1)

cql_query = ["CREATE KEYSPACE IF NOT EXISTS urlMap WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 2};",
            "CREATE TABLE urlMap.urlMap(short text PRIMARY KEY, long text);",
            "INSERT INTO urlMap.urlMap(short, long) VALUES ('dsh', 'https://shuhao.ca');"]

help_str = """commands:
    help: print this help
    exit: exit the program
    env: realod the .env file
    -------------------------
    cass: start cassandra cluster
    swarm: make a docker swarm
    deploy: deploy the stack
    rm: remove the stack
    status: check the status of the stack
    -------------------------
    run: cassandra + swarm + deploy
    stop: stop the stack and the cassandra cluster
    purge: purge the cassandra data"""


DOCKER_MANAGER = ''
DOCKER_HOSTS = []

def read_env():
    global DOCKER_MANAGER
    global DOCKER_HOSTS
    load_dotenv()
    DOCKER_MANAGER = os.getenv("MASTER_HOST")
    DOCKER_HOSTS = os.getenv("CASSANDRA_CLUSTER").split(",")
    try:
        DOCKER_HOSTS.remove(DOCKER_MANAGER)
    except ValueError:
        pass
    print(f"DOCKER_MANAGER: {DOCKER_MANAGER}")
    print(f"DOCKER_HOSTS: {DOCKER_HOSTS}")

def print_help():
    print(help_str)

def cassandra_cluster():
    subprocess.run(["./startCluster", DOCKER_MANAGER, *DOCKER_HOSTS])
    for query in cql_query:
        subprocess.run(["docker", "exec", "cassandra-node", "cqlsh", "-e", query])

def docker_swarm():
    subprocess.run(["./makeSwarm.py", DOCKER_MANAGER, *DOCKER_HOSTS])

def docker_stack_deploy():
    os.environ["MASTER_HOST"] = DOCKER_MANAGER
    os.environ["CASSANDRA_CLUSTER"] = DOCKER_MANAGER + "," + ",".join(DOCKER_HOSTS)
    subprocess.run(["docker", "stack", "deploy", "-c", "docker-compose.yml", "a2"])

def docker_stack_remove():
    subprocess.run(["docker", "stack", "rm", "a2"])

def stop_cassandra_cluster():
    subprocess.run(["./stopCluster", DOCKER_MANAGER, *DOCKER_HOSTS])

def remove_stack():
    subprocess.run(["docker", "stack", "rm", "a2"])

def show_stack():
    subprocess.run(["docker", "stack", "ps", "a2"])

def purge_db():
    subprocess.run(["ssh", f"student@{DOCKER_MANAGER}", "echo uoftnmsl | sudo -S rm -rf /home/student/cassandra/*"])
    for host in DOCKER_HOSTS:
        subprocess.run(["ssh", f"student@{host}", "echo uoftnmsl | sudo -S rm -rf /home/student/cassandra/*"])
    print('')

def read_command():
    try:
        while True:
            print("A2> ", end="")
            command = input()
            if command == "exit":
                break
            if command == "help":
                print_help()
            if command == "env":
                read_env()
            if command == "cass":
                cassandra_cluster()
            if command == "swarm":
                docker_swarm()
            if command == "deploy":
                docker_stack_deploy()
            if command == "rm":
                docker_stack_remove()
            if command == "status":
                show_stack()
            if command == "run":
                cassandra_cluster()
                docker_swarm()
                docker_stack_deploy()
            if command == "stop":
                remove_stack()
                stop_cassandra_cluster()
            if command == "purge":
                purge_db()
    except KeyboardInterrupt:
        print("exit.")
        exit(0)


if __name__ == "__main__":
    read_env()
    read_command()