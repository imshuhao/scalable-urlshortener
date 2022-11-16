#!/usr/bin/python3
import time
import logging
from cassandra.cluster import Cluster
from redis import Redis, RedisError

insert_statement = "INSERT INTO urlmap (short, long) VALUES (%s, %s);"

# redis_host = os.environ['REDIS_HOST']
# cassandra_cluster = [h.strip() for h in os.environ['CASSANDRA_CLUSTER'].split(',')]

redis_sentinel = [(s.strip(), 26379) for s in os.environ['REDIS_SENTINEL'].split(',')]
cassandra_cluster = [h.strip() for h in os.environ['CASSANDRA_CLUSTER'].split(',')]

cluster = Cluster(cassandra_cluster)
session = cluster.connect('urlmap')

sentinel = Sentinel(redis_sentinel, socket_timeout=2)

logging.basicConfig(level=int(os.environ['LOGGING_LEVEL']))

while True:
    try:
        shortResource = sentinel.master_for("mymaster", socket_timeout=2).blpop(keys=['queue'], timeout=0)
        shortResource = shortResource[1].decode('utf-8')
        
        logging.debug(msg="Received shortResource: " + shortResource)
        
        longResource = sentinel.slave_for("mymaster", socket_timeout=2).get(shortResource)
        logging.debug(msg="Retrieved longResource: " + longResource.decode('utf-8'))
        
        if longResource:
            longResource = longResource.decode('utf-8')
            session.execute(insert_statement, [shortResource, longResource])
            logging.debug(msg="Inserted shortResource: " + shortResource + ", longResource: " + longResource)
            
    except KeyboardInterrupt:
        logging.debug(msg="KeyboardInterrupt")
        session.shutdown()
        exit(0)
    except RedisError as e:
        logging.debug(msg=e)
        time.sleep(5)
        continue
    except Exception as e:
        logging.error(msg=e)
        exit(1)
