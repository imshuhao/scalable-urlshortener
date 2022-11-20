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
- Picture: (https://i.imgur.com/DFw1KCK.png)
(https://imgur.com/gallery/y5sCP9y)


### Application flow: PUT request
- Similarly for PUT requests, they are load balanced by docker. Since redis master is the
only redis server that can write, requests will only go to redis master and never to replicas.
- The redis master responds immediately to the PUT requests, caching it on its redis server.
This will soon be automatically replicated to other redis replicas. 
- Cassandra writes are queued in a blocking list on redis servers. A writer program wakes up periodically, or when master is idle, to perform inserts into cassandra databases. 
- Caching writes is advantegous because cassandra writes to disk, which takes longer to complete compared to redis caching in memory. 
- Picture: (https://i.imgur.com/JaCpdJr.png)
(https://imgur.com/gallery/SDp1gVl)


### Application structure: redis
- The redis server is made up of masters and replicas, and sentinels will watch over masters
for failovers. 
- Each master will persist data to disk and can have an arbitiary number of replicas. The master
is aware of its replicas ip and port.
- Replicas will not have persistance and will automatically replicate from its master. 
- Both redis master and replicas will evict data using allkeys-random as memory is getting used up.
- Sentinels can watch over masters for failovers. They can auto-discover masters' replicas and other
sentinels watching over the same master. It can also determine the state of replicas.
- Picture (https://i.imgur.com/W2VrNE4.png)
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
- Picture: (https://i.imgur.com/og4Pszk.png)
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
- Redis relys on memory and will have to evict keys using allkeys-random if memory is getting used up.


# Application analysis: testing
- Testing scripts: writeTest.py


### Discussion of each of the following with respect to your system.
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
	- GET Requests are cached by redis and replicated across all replicas. It is also written to cassandra cluster
	- PUT requests are queued in redis master, and  writers periodically wake up to perform queued
	writes to cassandra. In the meanwhile PUT requests will be cached and replicated in redis.
- [0] 1 Availability
	- When a hosts fails, requests will be redirected by docker as a part of load balancing.
	- If a redis master dies, redis sentinel will re-elect master as explained above to ensure write requests can be processed.
	- Docker will also restart any failing containers.
- [0] 1 Data replication
	- Data replication is automatically handled by redis replicas and cassandra cluster.
	- Redis uses complete replication and evict keys using allkeys-random as memory is used up.
- [0] 1 Load balancing
	- Requests will be automatically load balanced by docker among the url shortners.
	- Redis sentinels will automatically load balance redis requests from url shortners.
- [0] 1 Caching
	- Redis is known for fast reads with caching. 
	- In this application writes to cassandra are queued and a writer wakes up periodically to 
	perform writes to cassandra. This improves write throughput at a cost of consistancy.
- [0] 1 Process disaster recovery
	- Docker will automatically restart any failing container, ensuring availability.
	- In case of a redis master going down, redis sentinels will re-elect master to ensure that write requests can still be performed.
- [0] 1 Data disaster recovery
	- Both redis and cassandra servers are data persistant by storing data on a mounted disk in container.
	This means if the program crashes, we can still recover from disk.
	Cassandra is in a cassandra cluster, which means data will be replicated across all cassandra servers.
	If one cassandra nodes lost its data, data could still be recovered from other nodes in the cluster.
- [0] 1 Orchestration
	- We have a script that automatically starts, stops, and manages all services, including cassandra cluster, docker swarm and services on stack.
- [0] 1 Healthcheck
	- The health checker will periodically pings the services to check if they are down, by translating docker
	built in health check feature to user-friendly web interface.
- [0] 1 Horizontal scalability
	- The system takes advantage of additional hosts and adds them to the cluster.
		- Additional cassandra nodes means more storage for data. We can keep more data in our bank.
		This also means cassandra is more available; even if some nodes become unavailable, it is more likely that
		we still have some nodes online with the additional nodes.
		- Redis also benefit from additional hosts. As we get more nodes, we can start to hash requests and
		direct them to different masters that is responsible for that hash, each master having its own replicas.
		This means we have more memory space available, and redis servers are less likely to have to evict data
		as each master is responsible for less data. Generally improves throughput as more data will be cached.
		- Replicas will also be able to more quickly replicate new data as requests are hashed, because
		their master is responsible for less data, and replicas replicate less data. This leads to increased
		consistency as replicas will be more up-to-date.
		- More redis sentinels means higher availablity, as more sentinel watch over masters and failures can be
		more accurately detected. Re-electing new masters promptly will lead to increased availablity for writes
		as the time of having no master is decreased.
		- More writers to cassandra result in increased consistency, because queued write requests will be
		written to cassandra more promptly. So the time between writes being queued in redis and write is 
		performed in cassandra is shortened, and requests are more likely to get consistent response.
		- Docker automatically load balance for url shortners, and thus the system is able to handle more 
		requests simutaniously, as each system is less loaded.
- [0] 1 Vertical scalability
	- CPU benefit: Overall performance boost to all parts of system. More CPU cycles means the service
	gets more attention and is able to execute more instructions per second.
		- Docker can load balance for a larger amount of requests, because CPU is used to redirect requests
		to available hosts, and a better CPU means a higher capacity.
		- url shortners will be able to query redis and cassandra faster, as more clock cycles help the
		program advance in the process of parsing the request and fetching static data.
		- redis will be able to fetch data faster. Although redis is known for caching in memory, additional
		CPU cycles can help with finding the key value in memory faster.
		- redis replicas can sync with its master faster, as data is transferred and processed faster.
		- redis sentinels can also re-elect masters faster, because it can evaulate replicas for master
		eligibility faster.
	- RAM benefit: 
		- More throughput: redis having larger memory means more data can be cached. Less requests need to
		contact cassandra,, and redis can answer for more requests, where data is fetched faster
		than in cassandra because of fast memory reads/writes compared to disk IO.
		Redis can also fetch from and write to memory faster, if memory hardware is upgraded.
		- More services: we can run more services on each machine, as each service takes up some memory,
		more memory means more service capacity for each individual machine.
	- Disk benefit
		- Cassandra benefits from this by reading and writing to disk faster. As a result the application
		will experience increased throughput because requests that need to be read or written to cassandra
		takes less time to complete.
		- Additional disk space means we can store more data on disks for cassandra. Also Redis will have a 
		large persistent capacity.

### Discussing the system's performance

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