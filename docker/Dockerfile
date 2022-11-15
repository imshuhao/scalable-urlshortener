FROM python:alpine
WORKDIR /app
ADD ./app /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 80
ENV REDIS_HOST="localhost"
ENV CASSANDRA_CLUSTER="localhost"
CMD ["gunicorn", "-b", ":80", "-w", "2", "app:app", "--log-file=-"]
