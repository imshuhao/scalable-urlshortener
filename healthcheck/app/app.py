#!/usr/bin/python3
from cassandra.cluster import Cluster
from redis import Redis, RedisError
from redis.sentinel import Sentinel
from flask import Flask, request, redirect, render_template
import os, sys
import logging

app = Flask(__name__)
app.logger.addHandler(logging.FileHandler("/data/web.log"))
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

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8088)
