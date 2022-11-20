FROM python:alpine
WORKDIR /app
ADD ./app /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 80
HEALTHCHECK CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ping || exit 1
ENV REDIS_SENTINEL="redis-sentinel"
ENV CASSANDRA_CLUSTER=""
ENV LOGGING_LEVEL="10"
CMD ["gunicorn", "-b", ":80", "-w", "2", "app:app"]
