#!/usr/bin/python3
from multiprocessing import Process
import random, string, subprocess, requests

def run(num):
    for i in range(num):
        longResource = "http://" +''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100))
        shortResource = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        request="http://127.0.0.1:80/?short="+shortResource+"&long="+longResource

        subprocess.call(["curl", "-X", "PUT", request], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        request="http://127.0.0.1:80/"+shortResource
        
        subprocess.call(["curl", "-X", "GET", request], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    num_process = 8
    num_connection = 50000
    process_pool = []
    for i in range(num_process):
        process_pool.append(Process(target=run, args=(num_connection//num_process,)))
    start = time.time()
    for i in range(num_process):
        process_pool[i].start()
    for i in range(num_process):
        process_pool[i].join()
    end = time.time()
    print("time: {}".format(end - start))
