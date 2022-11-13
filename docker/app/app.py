#!/usr/bin/python
# https://pypi.org/project/cassandra-driver/
# https://docs.datastax.com/en/developer/python-driver/3.24/getting_started/
from cassandra.cluster import Cluster
from redis import Redis, RedisError
import time
from flask import Flask, request
import os
import socket

redis = Redis(host="redis", db=0, socket_connect_timeout=2, socket_timeout=2)

'''
profile = ExecutionProfile(
	load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
	retry_policy=DowngradingConsistencyRetryPolicy(),
	consistency_level=ConsistencyLevel.LOCAL_QUORUM,
	serial_consistency_level=ConsistencyLevel.LOCAL_SERIAL,
	request_timeout=15,
	row_factory=tuple_factory
)
# Can pass in execution profile 
cluster = Cluster(execution_profiles={EXEC_PROFILE_DEFAULT: profile})
'''

cluster = Cluster(['IP1', 'IP2'])
# session = cluster.connect()
session = cluster.connect('cassandratutorial')

# session.set_keyspace('users')
# or you can do this instead
# session.execute('USE users')

def timeCassandra(yearStart, yearEnd):
	userids = [ "userid"+str(i) for i in range(10) ]
	start_time = time.time()
	count = 0
	
	insert_statement = """
	INSERT INTO calendar (userid, year, month, day, event)
	VALUES (%s, %s, %s, %s, %s);
	"""
	for userid in userids:
		for year in range(yearStart,yearEnd):
			for month in range(1,13):
				for day in range(1,32):
					event = "{} {} {} {}".format(userid, year, month, day)
					session.execute(insert_statement, (userid, year, month, day, event))
					count = count + 1
	
	end_time = time.time()
	report = "Cassandra: {} inserts in {} seconds".format(count, (end_time - start_time))
	print(report)
	return report

def timeRedis(yearStart, yearEnd):
	userids = [ "userid"+str(i) for i in range(10) ]
	start_time = time.time()
	count = 0
	for userid in userids:
		for year in range(yearStart,yearEnd):
			for month in range(1,13):
				for day in range(1,32):
					event = "{} {} {} {}".format(userid, year, month, day)
					key = "{} {} {} {}".format(userid, year, month, day)
					redis.set(key, event)
					count = count + 1
	end_time = time.time()
	report = "Redis: {} inserts in {} seconds".format(count, (end_time - start_time))
	print(report)
	return report

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():
	html = """
<form>
	<input type="text" name="yearStart" />
	<input type="text" name="yearEnd" />
	<input type="submit" />
</form>
"""
	html=""
	args = request.args
	if 'yearStart' in args and 'yearEnd' in args:
		yearStart = int(request.args['yearStart'])
		yearEnd = int(request.args['yearEnd'])
		report1=timeCassandra(yearStart, yearEnd)
		report2=timeRedis(yearStart, yearEnd)
		html="Execution Results:\n {}\n{}\n".format(report1, report2)

	return html

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)

