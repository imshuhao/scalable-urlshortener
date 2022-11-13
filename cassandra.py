#!/usr/bin/python
# https://pypi.org/project/cassandra-driver/
# https://docs.datastax.com/en/developer/python-driver/3.24/getting_started/
from cassandra.cluster import Cluster

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
'''

cluster = Cluster(execution_profiles={EXEC_PROFILE_DEFAULT: profile})
session = cluster.connect()

cluster = Cluster(['10.11.12.2', '10.11.12.3'])

session = cluster.connect()
session = cluster.connect('cassandraTutorial')

# session.set_keyspace('users')
# or you can do this instead
# session.execute('USE users')

userids = [ "userid"+i for i in range(1000) ]

insert_statement = """
INSERT INTO calendar (userid, year, month, day, event)
VALUES (%s, %s, %s, %s, %s);
"""
for userid in userids:
	for year in range(2020,2022):
		for month in range(1,13):
			for day in range(1,32):
				event = "{} {} {} {}".format(userid, year, month, day)
				session.execute(insert_statement, (userid, year, month, day, event))




