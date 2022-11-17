#!/usr/bin/python3.8
import subprocess
import sys

if (len(sys.argv) < 2):
    print (f"Usage: {sys.argv[0]} IP1 IP2 IP3...")
    sys.exit(1)

manager = sys.argv[1]
swarm_leave_cmd = "docker swarm leave --force &>/dev/null;"
swarm_init_cmd = "docker swarm init --advertise-addr " + manager + "|grep 'docker .*[0-9]'"
cmd = ["ssh", "student@"+manager, swarm_leave_cmd+swarm_init_cmd]
swarm_join_cmd = subprocess.run(cmd, capture_output=True).stdout.decode('utf-8').strip()
print(swarm_join_cmd)

for i in range(2, len(sys.argv)):
    subprocess.run(["ssh", "student@"+sys.argv[i], swarm_leave_cmd+swarm_join_cmd])
