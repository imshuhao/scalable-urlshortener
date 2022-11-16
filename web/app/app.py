#!/usr/bin/python3
from cassandra.cluster import Cluster
from redis import Redis, RedisError
from redis.sentinel import Sentinel
from flask import Flask, request, redirect, render_template
import os, sys
import logging
app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))


app.logger.setLevel(int(os.environ['LOGGING_LEVEL']))

redis_sentinel = [(s.strip(), 26379) for s in os.environ['REDIS_SENTINEL'].split(',')]
cassandra_cluster = [h.strip() for h in os.environ['CASSANDRA_CLUSTER'].split(',')]
app.logger.debug(redis_sentinel)
app.logger.debug(cassandra_cluster)

cluster = Cluster(cassandra_cluster)
session = cluster.connect('urlmap')

sentinel = Sentinel(redis_sentinel, socket_timeout=2)

query = "SELECT long FROM urlmap WHERE short = %s;"

@app.route("/", methods=['GET'])
def index():
	return render_template('index.html')

@app.route("/<shortResource>", methods=['GET'])
def getResource(shortResource):
	longResource = None
	try:
		longResource = sentinel.slave_for("mymaster", socket_timeout=2).get(shortResource)
	except RedisError:
		app.logger.debug("Error: cannot get value from Redis")
	if not longResource:
		try:
			longResource = session.execute(query, [shortResource]).one().long
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
		sentinel.master_for("mymaster", socket_timeout=2).set(shortResource, longResource)
		sentinel.master_for("mymaster", socket_timeout=2).rpush('queue', shortResource)
	except RedisError:
		app.logger.debug("Error: cannot set or rpush value to Redis")
	return "Success", 201

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)
