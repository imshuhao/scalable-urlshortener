FROM python:alpine
WORKDIR /app
ADD ./app /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 80
ENV REDIS_SENTINEL="redis-sentinel"
ENV CASSANDRA_CLUSTER="10.11.1.114,10.11.1.115,10.11.1.23"
ENV LOGGING_LEVEL="10"
CMD ["gunicorn", "-b", ":80", "-w", "2", "app:app"]
