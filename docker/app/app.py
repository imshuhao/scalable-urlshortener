#!/usr/bin/python3
from cassandra.cluster import Cluster
from redis import Redis, RedisError
from flask import Flask, request, redirect, render_template
import os, sys
import logging
app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

redis_host = os.environ['REDIS_HOST']
cassandra_cluster = [h.strip() for h in os.environ['CASSANDRA_CLUSTER'].split(',')]


redis = Redis(host=redis_host, db=0, socket_connect_timeout=2, socket_timeout=2)
app.logger.debug(cassandra_cluster)

cluster = Cluster(cassandra_cluster)
session = cluster.connect('urlmap')

insert_statement = """
INSERT INTO urlmap (short, long)
VALUES (%s, %s);
"""

select_statement = """
SELECT long FROM urlmap
WHERE short = %s;
"""


@app.route("/", methods=['GET'])
def hello():
	return render_template('index.html')

@app.route("/<shortResource>", methods=['GET'])
def getResource(shortResource):
	longResource = None
	try:
		longResource = redis.get(shortResource)
	except RedisError:
		app.logger.debug("Error: cannot get value from Redis")
	if not longResource:
		try:
			longResource = session.execute(select_statement, [shortResource]).one().long
		except AttributeError:
			pass
		except Exception as e:
			return str(e), 500
	if longResource:
		try:
			redis.set(shortResource, longResource)
		except RedisError:
			app.logger.debug("Error: cannot set value to Redis")
		return redirect(longResource, code=307)
	return "Not Found", 404

@app.route("/", methods=['PUT'])
def putResource():
	longResource = request.args.get('long')
	shortResource = request.args.get('short')
	if not (longResource and shortResource):
		return "Bad Request (empty field)", 400
	if "://" not in longResource:
		return "Bad Request (not a URL)", 400
	try:
		session.execute(insert_statement, [shortResource, longResource])
	except:
		return "Error: cannot connect to Cassandra", 500
	try:
		redis.delete(shortResource)
	except RedisError:
		app.logger.debug("Error: cannot delete value from Redis")
	return "Success", 201

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)
