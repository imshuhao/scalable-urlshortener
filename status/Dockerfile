FROM python:alpine
WORKDIR /app
ADD ./app /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 8888
HEALTHCHECK CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8888/ping || exit 1
CMD ["gunicorn", "-b", ":8888", "app:app"]
