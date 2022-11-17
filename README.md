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


### Application flow: PUT request
- Similarly for PUT requests, they are load balanced by docker. Since redis master is the
only redis server that can write, requests will only go to redis master and never to replicas.
- The redis master responds immediately to the PUT requests, caching it on its redis server.
This will soon be automatically replicated to other redis replicas. 
- Cassandra writes are queued in a blocking list on redis servers. A writer program wakes up periodically, or when master is idle, to perform inserts into cassandra databases. 
- Caching writes is advantegous because cassandra writes to disk, which takes longer to complete compared to redis caching in memory. 


### Application structure: redis
- The redis server is made up of masters and replicas, and sentinels will watch over masters
for failovers. 
- Each master will persist data to disk and can have an arbitiary number of replicas. The master
is aware of its replicas ip and port.
- Replicas will not have persistance and will automatically replicate from its master. 
- Sentinels can watch over masters for failovers. They can auto-discover masters' replicas and other
sentinels watching over the same master. It can also determine the state of replicas.


### Application fault tolorence: redis master re-election
- In the event of a redis master being out of reach of a sentinel, it will subjectively mark
the master as down (s_down). 
- If the number of sentinels on the same master and marking the master as s_down is equal to or 
greater than the set quorum (default to 2), the master will be considered as objectively down 
(o_down).
- At this point the sentinels start to vote for a new master. When a master is elected, all
existing replicas will be alerted by the sentinels and replace its old master with the new master. 
- The old master will be alerted by the sentinels and become a replica of the new master. 


# Application analysis: strength
- Load balance requests for url shortners automatically handled by docker.
- Fault Tolorence: docker restarts any failing url shortner, redis, and cassandra.
- High availability: Redis sentinel re-electing masters ensures writes 
- High consistency: Redis automatically replicates data from master servers.
- High scalability: 
- Caching: Redis is very fast for read requests because of caching.
- Improved writing: Queuing writes to databases improves write throughput.



# Application analysis: weakness
- The new redis master elected by sentinels will not have persistance to disk, since it
was originally a replica service without disk mounting.
- If a redis master goes down before the writer gets to perform writes or the queue of writes
gets replicated, data could be lost.



### 0/3 Diagram showing
- [0] 1 Application system

![Application system](https://s2.loli.net/2022/11/01/Otzamd1fJNnHSBP.jpg)

- [0] 1 Monitoring system

![Application system](https://s2.loli.net/2022/11/01/nzNXUL5F7otwIT4.jpg)

- [0] 1 Data flow

![Application system](https://s2.loli.net/2022/11/01/twzShrolxaMbI7A.jpg)

### 0/14 Discussion of each of the following with respect to your system.
- For each point, as appropriate, show an appropriate diagram, list performance guarantees, discuss code/architecture choices.
- Example:
	- Availability:
		- the availability guarantees your system provides
		- the architectural choices made to implement this
	- Data Partitioning:
		- diagram explaining how data is partitioned
		- outline how your code implements this, for example,
		if you hash, then which hash algorithm
- [0] 1 Consistency
	- Request is hashed to specific host for GET and PUT
	requests, ensuring requests for the same short resource
	will always return the same answer of the most recent write.
- [0] 1 Availability
	- When a hosts fails, requests will be re-hashed and redirected
	to remaining hosts. This ensures every request will receive
	a non-error response. 
- [0] 1 Partition tolerance
	- Data will be re-partitioned and sync'ed between hosts via
	central DB periodically. If cannot partition(due to any reason), 
	system will continue to run without interrpution but consistency
	may not be guarenteed.
- [0] 1 Data partitioning
	- Data will be MD5 hashed and the first 2 bytes will be converted
	into integer. Distribution among alive hosts will be determined 
	by modding the result integer with number of host alive.

	![partition.jpeg](https://s2.loli.net/2022/11/01/tn2wGsWoIYdUheA.jpg)
	
- [0] 1 Data replication
	- Central DB will have a replica of the collective data set, and 
	will be updated periodically if a host received new data.
- [0] 1 Load balancing
	- Requests will be MD5 hashed and redirected based on hash result.
	This is a performance improvement as work load from requests is
	balanced among alive hosts.
- [0] 1 Caching
	- Both the load balancer and the URLShortner will have a cache
	of recent requests. If hits return from cache. This is a performance
	improvement since requests can be answered from cache without needing
	to forward to URLShornter or database.
- [0] 1 Process disaster recovery
	- Monitoring system will monitor and restart dead processes, which includes
	the load balancer, central DB, and URLShortner.
- [0] 1 Data disaster recovery
	- If local database is destroyed, URLShortner will restore part/all of it from
	memory, additionally the central DB will have a replica of all data,
	and can be used to restore databases.
- [0] 1 Orchestration
	- Monitor system have a built in orchestration feature, where it can
	start the cluster including load balancer, central DB, and URLShortners. It can
	also shutdown the cluster easily. Adding and deleting hosts can be done
	via a bash script.
- [0] 1 Healthcheck
	- Monitoring system will periodically ping hosts to check if alive. 
	Additionally the central DB will udp broadcast its heartbeat in a port
	that the monitor system is listening. System health is displayed in
	a simple UI of the monitoring system.
- [0] 1 Horizontal scalability
	- The system takes advantage of additional hosts and adds them to the cluster.
		- Central DB will re-partition data based on number of alive hosts and distribute
		the parition among them, making each host more room in data storage. 
		Thus the system benefit from addtional capacities. 
		- System gains more throughput since load balancer is able to distribute
		requests among added hosts, meaning the whole cluster is overall less loaded
		and more efficient.
- [0] 1 Vertical scalability
	- CPU benefit: Overall performance boost to all parts of system. Load balancer can
	hash and forward request faster; DB can communicate and sync data among hosts faster;
	URLShortner can respond faster to requests.
	- RAM benefit: Load balancer and URLShortner have larger memory and cache, potentially
	more requests will hit the cache.
	- Disk benefit: URLShortner and central DB will have larger capacity in database storage,
	storing more data.
- [0] 1 Well formatted document
	- :D

### 0/4 Discussing the system's performance

- [0] 1 Graph showing performance of system under load1

![loadTimeSeries10k.jpg](https://s2.loli.net/2022/11/01/5sXe8YpStTjyRAZ.jpg)

- [0] 1 Analysis of system performance under load1
	All requests finish quickly in around 1ms under load of 10000 requests of 8 concurrency level, 
	with a few outliers going beyond 4ms.

- [0] 1 Graph showing performance of system under load2

![loadTimeSeries50k.jpg](https://s2.loli.net/2022/11/01/S45DP1rnbXmtg3B.jpg)

- [0] 1 Analysis of system performance under load2
	Most requests finish in less than 3 ms, under load of 50000 requests of 8 concurrency level.
	However, the last 10% requests take longer to complete as the server gets loaded and
	wait time increases.

### 0/4 Discussing the system's scalability

- [0] 1 Number of hosts vs read requests per second
	- Read requests per second should scale proportionally with number of hosts,
	because the load balancer distribute the request loads amongs
	hosts. For example, it takes 6.8 seconds to finish x requests
	for 4 hosts, while it takes 8.5 seconds for the same requests
	at 3 hosts. Lost 25% of hosts so it takes 25% more time, approximately.
- [0] 1 Number of hosts vs write requests per second
	- The Number of hosts vs write requests per second should scale
	similarly to read requests, because all write requests are hashed
	by the load balancer and forwarded to specific hosts. As the number of 
	hosts increase, write requests per second should also increase as requests
	distributed to each hosts decrease respectively.
- [0] 1 Number of hosts vs data stored
	- Data stored will also increase as number of hosts increase, since each
	host contains a partition of the whole data set. The addition of hosts means
	that each host need to carry less data, in other words increasing data storage
	capacity. The central DB will continue to be a transit hub for data sync.

### 0/2 Discussion of the tools used during testing. Listing them is not enough.
You must define each tool used, and how you used it
- apache bench
	- ab -n 4000 -c 8 -g load.tsv http://dh2020pc29:8086/00000000000000000000000000000000000000
		- -n to define number of requests.
		- -c to define number of concurrent requests.
		- -g output to load.tsv
		- url to test
	- Output file
		- Start time: human readable time at the time of request
		- seconds: unix seconds since epoch
		- ctime: connection time in ms, time taken to fully establish connection
		- dtime: process time in ms, time taken to finish processing request
		- ttime: total time in ms, ctime+dtime
		- wait: waited time, time process waited to receive data after connection
	- Result:
		- 50000 requests with ab took 8 seconds with 8 concurrency level
		- most requests took less than 3 ms to complete, with 100% percentile being 6 ms
		- 6471 read / sec
