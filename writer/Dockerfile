FROM python:alpine
WORKDIR /app
ADD ./writer.py /app/writer.py
ADD ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
ENV REDIS_SENTINEL="10.11.1.114,10.11.1.115,10.11.1.23"
ENV CASSANDRA_CLUSTER="10.11.1.114,10.11.1.115,10.11.1.23"
ENV LOGGING_LEVEL = "10"
CMD ["python3", "writer.py"]
