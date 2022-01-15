#FROM quay.io/prometheus/node-exporter:v1.1.2
FROM python:3.6
MAINTAINER unixwords.com
 
# Creating Application Source Code Directory
RUN mkdir -p /python_test/src
# Setting Home Directory for containers
WORKDIR /python_test/src
# Installing python dependencies
COPY ./pyapp/requirements.txt /python_test/src
#RUN pip install — no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt
# Copying src code to Container
COPY ./pyapp/node_exporter /python_test/src/node_exporter
COPY ./pyapp/write-file.py /python_test/src/write-file.py
COPY ./pyapp/heatmap.py /python_test/src/heatmap.py
COPY ./pyapp/config.conf /python_test/src/config.conf
# Application Environment variables
ENV APP_ENV development
# Exposing Ports
#EXPOSE 4025
# Setting Persistent data
#VOLUME [“/app-data”]
# Running Python Application
#CMD [“python3”, “write-file.py”]
CMD [ "/bin/sh" ]
