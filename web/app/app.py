#!/usr/bin/python3
from cassandra.cluster import Cluster
from redis import Redis, RedisError
from redis.sentinel import Sentinel
from flask import Flask, request, redirect, render_template
import os, sys
import logging

app = Flask(__name__)
app.logger.basicConfig(filename='/data/log.txt')
# app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(int(os.environ['LOGGING_LEVEL']))

redis_sentinel = [(s.strip(), 26379) for s in os.environ['REDIS_SENTINEL'].split(',')]
cassandra_cluster = [h.strip() for h in os.environ['CASSANDRA_CLUSTER'].split(',')]

cluster = Cluster(cassandra_cluster)
session = cluster.connect('urlmap')

sentinel = Sentinel(redis_sentinel, socket_timeout=2)
app.logger.debug(sentinel.master_for("mymaster", socket_timeout=2))

select_query = "SELECT long FROM urlmap WHERE short = %s;"
insert_query = "INSERT INTO urlmap (short, long) VALUES (%s, %s);"


@app.route("/", methods=['GET'])
def index():
	return render_template('index.html')

@app.route("/<shortResource>", methods=['GET'])
def getResource(shortResource):
	longResource = None
	redis_not_found = True
	try:
		longResource = sentinel.slave_for("mymaster", socket_timeout=2).get(shortResource)
		redis_not_found = False
	except RedisError as e:
		app.logger.debug("Error: cannot get value from Redis")
		redis_not_found = True
	
	if not longResource:
		try:
			longResource = session.execute(select_query, [shortResource]).one().long
		except AttributeError:
			pass
		except Exception as e:
			app.logger.error(str(e))
			return "500 Internal Server Error", 500
	if longResource and redis_not_found:
		try:
			sentinel.master_for("mymaster", socket_timeout=2).set(shortResource, longResource)
		except RedisError:
			app.logger.debug("Error: cannot set value to Redis")
	if not longResource:
		return "Not Found", 404
	return redirect(longResource, code=307)
	

@app.route("/", methods=['PUT'])
def putResource():
	longResource = request.args.get('long')
	shortResource = request.args.get('short')
	if not (longResource and shortResource):
		return "Bad Request (empty field)", 400
	if "://" not in longResource:
		return "Bad Request (not a URL)", 400
	try:
		master = sentinel.master_for("mymaster", socket_timeout=2)
		master.set(shortResource, longResource)
		master.rpush('queue', shortResource)
	except RedisError as e:
		app.logger.error(str(e))
		try:
			session.execute(insert_query, [shortResource, longResource])
		except Exception as e:
			app.logger.error(str(e))
			return "503 Service Unavailable", 503
	return "Success", 201


if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)
