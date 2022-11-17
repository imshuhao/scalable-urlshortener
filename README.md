# CSC409A2 Report

### Application overview
- List of tools used:
	- Docker Engine - Community Version: 20.10.7, API version: 1.41 (minimum version 1.12)
		- Redis official image
			- For caching requests, very fast response time
		- Redis sentinel offical image
			- For high availablility, fault tolorence
		- Cassandra official image
			- For database, persistance to disk
		- URL Shortner custom image
			- Python flask server, main application
		- Cassandra writer
			- For performance improvements on writes by caching cassandra writes
	- Ubuntu 18.04.6 LTS
	- python 3.8
		- gunicorn
		- Flask


### Application flow: GET request
- GET requests are managed by the url shortners, which run as docker containers, 
and thus requests are automatically load balanced by docker. 
- Docker maps ports 1:1 on port 80, which means port 80 inside the container will be
mapped to port 80 on the outside world. Even though url shortners live in containers while
exposing port 80, docker port mapping effectively creates services listening on port 80 outside.
- Url shortners will acquire addresses of redis sentinels, where they can receive information
about other redis servers including replicas and masters. GET requests will prioritize replicas,
since they are read-only, this acts as a load balancer between redis servers.
- If all redis servers are not available, or the request is not cached, it will try to 
retrive the data from the cassandra cluster. If successful, the application will cache the
result in redis servers, making it easier to access for later requests.
(https://i.imgur.com/DFw1KCK.png)
(https://imgur.com/gallery/y5sCP9y)


### Application flow: PUT request
- Similarly for PUT requests, they are load balanced by docker. Since redis master is the
only redis server that can write, requests will only go to redis master and never to replicas.
- The redis master responds immediately to the PUT requests, caching it on its redis server.
This will soon be automatically replicated to other redis replicas. 
- Cassandra writes are queued in a blocking list on redis servers. A writer program wakes up periodically, or when master is idle, to perform inserts into cassandra databases. 
- Caching writes is advantegous because cassandra writes to disk, which takes longer to complete compared to redis caching in memory. 
(https://i.imgur.com/JaCpdJr.png)
(https://imgur.com/gallery/SDp1gVl)


### Application structure: redis
- The redis server is made up of masters and replicas, and sentinels will watch over masters
for failovers. 
- Each master will persist data to disk and can have an arbitiary number of replicas. The master
is aware of its replicas ip and port.
- Replicas will not have persistance and will automatically replicate from its master. 
- Sentinels can watch over masters for failovers. They can auto-discover masters' replicas and other
sentinels watching over the same master. It can also determine the state of replicas.
(https://i.imgur.com/W2VrNE4.png)
(https://imgur.com/gallery/HOnKBQ4)


### Application fault tolorence: redis master re-election
- In the event of a redis master being out of reach of a sentinel, it will subjectively mark
the master as down (s_down). 
- If the number of sentinels on the same master and marking the master as s_down is equal to or 
greater than the set quorum (default to 2), the master will be considered as objectively down 
(o_down).
- At this point the sentinels start to vote for a new master. When a master is elected, all
existing replicas will be alerted by the sentinels and replace its old master with the new master. 
- The old master will be alerted by the sentinels and become a replica of the new master. 
(https://i.imgur.com/og4Pszk.png)
(https://imgur.com/gallery/TwFJPvf)


# Application analysis: strength
- Load balance requests for url shortners automatically handled by docker.
- Fault Tolorence: docker restarts any failing url shortner, redis, and cassandra.
- High availability: Redis sentinel re-electing masters ensures writes 
- High consistency: Redis automatically replicates data from master servers.
- Caching: Redis is very fast for read requests because of caching.
- Improved writing: Queuing writes to databases improves write throughput.


# Application analysis: weakness
- The new redis master elected by sentinels will not have persistance to disk, since it
was originally a replica service without disk mounting.
- If a redis master goes down before the writer gets to perform writes or the queue of writes
gets replicated, data could be lost.


# Application analysis: testing
- Testing scripts: writeTest.py
