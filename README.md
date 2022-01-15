# Heatmap to monitor ETCD health
Here, in this document I try to explain the steps and technologies behind coming up with an etcd-monitoring heatmap which could help anyone to predict if the cluster is healthy just by looking at the colors on heatmap, with green indicating good and red indicating bad health respectively. 
![hourly heatmap-etcd](https://user-images.githubusercontent.com/83866176/149630777-46792f3d-e084-4791-b686-44465310ceba.png)

The technologies used are : `Prometheus`, `Node Exporter`, `Grafana` and `Kubernetes`.

1. [Prometheus](https://prometheus.io/docs/introduction/overview/) is an open source systems monitoring solution with powerful metrics and efficient alerting mechanism. It collects and stores its metrics as time series data i.e metrics information is stored with the timestamp at which it was recorded. It can be accessed on port 9090 after successful installation. 
2. [Node Exporter](https://github.com/prometheus/node_exporter) is Prometheus’ metric exporter for OS and hardware metrics used primarily on unix systems (alternative for windows - windows exporter). It listens on port 9100.
3. [Grafana](https://grafana.com/docs/) is a powerful visualization and analytics tool for time series data. We can access the time series data scrapped and stored by Prometheus and perform various transformations on them and analyse it on this platform.
4. [Kubernetes](https://kubernetes.io/docs/home/) is a container orchestration tool that manages the deployment, up-scaling, down-scaling, etc of containerized applications. 

Firstly, why should such monitoring be required if Grafana provides developers with amusing graphs and visualizations of time series data? To answer that, let’s take an example to monitor ETCD within a kubernetes cluster. The basic metrics one would go for would be : Client Traffic in, Leader elections,etc. Imagine the hassle of going through each graph and observing discrepancies, and over that, imagine having to do that for ‘n’ number of cluster instances. The heatmap visualization would culminate all of the above and more to provide developers and testers with one stop destination to monitor their clusters. 

## Steps to build the heatmap
1. Configure your system/instance with prometheus and enable node exporter. ([click here](https://netcorecloud.com/tutorials/setup-prometheus-and-exporters/) to follow the installation guide)
2. Install and configure grafana ([click here](https://grafana.com/docs/grafana/latest/installation/debian/) for installation steps)
3. Install Hourly heatmap plugin on grafana
   Hourly heatmap aggregates data into buckets of day and hour to analyse activity or traffic during the day. It can easily be installed in a few steps. 
   [Click Here](https://grafana.com/grafana/plugins/marcusolsson-hourly-heatmap-panel/?tab=installation) to go to the website for installation guide. 
   Once installed, it should be visible on your Grafana port right away under different types of visualizations. ![image1](https://user-images.githubusercontent.com/83866176/149631560-5564ba48-38ec-4b75-a31e-8ebd426a3d0f.png)
4. Build a docker image to get custom metrics from your kubernetes cluster.
   
   *Dockerfile image* : bejoyr/heatmapvsoc:v3
  ```
  #FROM quay.io/prometheus/node-exporter:v1.1.2
  FROM python:3.6
  MAINTAINER unixwords.com

  #Creating Application Source Code Directory
  RUN mkdir -p /python_test/src
  #Setting Home Directory for containers
  WORKDIR /python_test/src
  #Installing python dependencies
  COPY ./pyapp/requirements.txt /python_test/src
  #RUN pip install — no-cache-dir -r requirements.txt
  RUN pip install -r requirements.txt
  #Copying src code to Container
  COPY ./pyapp/node_exporter /python_test/src/node_exporter
  COPY ./pyapp/write-file.py /python_test/src/write-file.py
  COPY ./pyapp/heatmap.py /python_test/src/heatmap.py
  COPY ./pyapp/config.conf /python_test/src/config.conf
  #Application Environment variables
  ENV APP_ENV development
  #Exposing Ports
  #EXPOSE 4025
  #Setting Persistent data
  #VOLUME [“/app-data”]
  #Running Python Application
  #CMD [“python3”, “write-file.py”]
  CMD [ "/bin/sh" ]
  ```
  Contents of the Dockerfile :
  - config file : This file contains the weights that can be adjusted according to the priority of the metrics aggregated for our monitoring model.
    The metrics used for the process are : `Etcd_wal_fsync`, `etcd_db_fsync`, `etcd_file_descriptor`, `etcd_leader_election`, `etcd_client_trafffic_in`, `etcd_database_size`. 

    A sample config file : 
    ```
    [weights]
    wt_etcd_wal_fsync = 0.3
    wt_etcd_db_fsync = 0.2
    wt_etcd_file_descriptor = 0.1
    wt_etcd_leader_election = 0.3
    wt_etcd_client_traffic_in = 0.05
    wt_etcd_database_size = 0.05

    [time]
    duration='[1h]'
    ```
  - Python file to generate custom metrics for node exporter to expose
    ```
    #!/usr/bin/env python3
    import datetime
    import time
    import requests
    from csv import writer
    from csv import reader
    from decimal import Decimal
    import os
    import configparser

    PROMETHEUS = 'http://prometheus-service.monitoring:9090/'

    parser = configparser.ConfigParser()
    parser.read("./config.conf")

    wt_etcd_wal_fsync = parser["weights"]["wt_etcd_wal_fsync"]
    wt_etcd_db_fsync = parser["weights"]["wt_etcd_db_fsync"]
    wt_etcd_file_descriptor = parser["weights"]["wt_etcd_file_descriptor"]
    wt_etcd_leader_election = parser["weights"]["wt_etcd_leader_election"]
    wt_etcd_client_traffic_in = parser["weights"]["wt_etcd_client_traffic_in"]
    wt_etcd_database_size = parser["weights"]["wt_etcd_database_size"]

    duration = parser["time"]["duration"]

    #print(wt_etcd_wal_fsync)
    #print(wt_etcd_db_fsync)
    #print(wt_etcd_file_descriptor)
    #print(wt_etcd_leader_election)
    #print(wt_etcd_client_traffic_in)
    #print(wt_etcd_database_size)
    #print(duration)
    
    metrics = ['etcd_wal_fsync','etcd_db_fsync','etcd_file_descriptor','etcd_leader_election','etcd_client_traffic_in','etcd_database_size']

    #Get response for each metric from Prometheus
    response_wal = requests.get(PROMETHEUS + '/api/v1/query',
      params={
        'query': 'job:etcd_disk_wal_fsync_duration_seconds_bucket:99percentile'})
    etcd_wal_fsync  = response_wal.json()['data']['result']

    response_db = requests.get(PROMETHEUS + '/api/v1/query',
      params={
        'query': 'job:etcd_disk_backend_commit_duration_seconds_bucket:99percentile'})
    etcd_db_fsync  = response_db.json()['data']['result']

    response_file_descriptor = requests.get(PROMETHEUS + '/api/v1/query',
      params={
        'query': 'job:process_open_fds:clone{instance=~"etcd-.+"}'})
    etcd_file_descriptor  = response_file_descriptor.json()['data']['result']

    response_leader_election = requests.get(PROMETHEUS + '/api/v1/query',
      params={
          'query': 'job:etcd_server_leader_changes_seen_total:changes1d'})
    etcd_leader_election  = response_leader_election.json()['data']['result']

    response_client_traffic_in = requests.get(PROMETHEUS + '/api/v1/query',
      params={
        'query': 'job:etcd_network_client_grpc_received_bytes_total:rate5m'})
    etcd_client_traffic_in  = response_client_traffic_in.json()['data']['result']

    response_database_size = requests.get(PROMETHEUS + '/api/v1/query',
      params={
        'query': 'job:etcd_debugging_mvcc_db_total_size_in_bytes:clone'})
    etcd_database_size  = response_database_size.json()['data']['result']

    etcd_wal_fsync = Decimal('{value[1]}'.format(**etcd_wal_fsync[0]))
    etcd_db_fsync = Decimal('{value[1]}'.format(**etcd_db_fsync[0]))
    etcd_file_descriptor = Decimal('{value[1]}'.format(**etcd_file_descriptor[0]))
    etcd_leader_election = Decimal('{value[1]}'.format(**etcd_leader_election[0]))
    etcd_client_traffic_in = Decimal('{value[1]}'.format(**etcd_client_traffic_in[0]))
    etcd_database_size = Decimal('{value[1]}'.format(**etcd_database_size[0]))

    #default scores of all metrics = 10
    etcd_score_wal_fsync = 10
    etcd_score_file_descriptor = 10
    etcd_score_leader_election = 10
    etcd_score_db_fsync = 10
    etcd_score_database_size = 10
    etcd_score_client_traffic_in = 10

    #Danger wal fsync duration > 10ms
    if etcd_wal_fsync > 0.01:
        etcd_score_wal_fsync = 0

    #Danger file descriptor > 1024
    if etcd_file_descriptor > 1024:
        etcd_score_file_descriptor = 0

    #Danger leader elections > 5 per day
    if etcd_leader_election > 5:
        etcd_score_leader_election = 0

    #Danger db_fsync > 40ms and Moderate danger 25-40ms
    if etcd_db_fsync > 0.04:
        etcd_score_db_fsync = 0
    elif etcd_db_fsync < 0.04 and etcd_db_fsync > 0.025:
        etcd_score_db_fsync = 5

    etcd_score = Decimal(wt_etcd_wal_fsync) * etcd_score_wal_fsync + Decimal(wt_etcd_db_fsync) * etcd_score_db_fsync + Decimal(wt_etcd_file_descriptor) * etcd_score_file_descriptor + Decimal(wt_etcd_leader_election) * etcd_score_leader_election + Decimal(wt_etcd_client_traffic_in) * etcd_score_client_traffic_in + Decimal(wt_etcd_database_size) * etcd_score_database_size
    
    print('etcd_score',etcd_score)

    ```
  The working is explained in the figure below and can be understood by observing the flow. The python file parses the configuration file to get the weights of the different metrics used for our monitoring. It then establishes a connection with the prometheus server which listens on port 9090 to get the values of metrics at that instant. The metric values then undergo a series of computational steps involving checking for thresholds to get the final etcd_score which is written into a special file(\*.prom) which would be used by node exporter to expose the custom metric value on its port from where prometheus can scrape it. This needs to be set up in a ***crontab*** fashion of events for the metric to insert data into the textfile-collector at regular intervals of time so that we get a time series data that can be visualized on grafana.
  (to enable textfile collector for custom metric we need to start node exporter with --collector.textfile.directory flag and set it equal to the special \*.prom file path)

![image2](https://user-images.githubusercontent.com/83866176/149632085-d73cb9c0-9738-424e-beee-7fc167116349.png)

   
5. Configure the image into a pod on your kubernetes cluster using the dokcker image name.
  ```
  apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubermatic.io/chart: heatmap-etcd
    prometheus.io/port: "9100"
    prometheus.io/scrape: "true"
  labels:
    app: heatmap-etcd
  name: heatmap-etcd
  namespace: monitoring
spec:
  containers:
  - name: heatmap-etcd
#    args: ["--collector.disable-defaults --collector.textfile.directory=/python_test/src"]
#    - --collector.textfile.directory=/python_test/src
    image: bejoyr/heatmapvsoc:v3
    command: ["/bin/bash"]
#    args: ["-c", "while true; do echo hello; sleep 10;done"]
    args: ["-c", "while true ; do  python3 heatmap.py > /python_test/src/heat.prom ; sleep 15; done"]
#    args: ["-c /bin/entrypt.sh" ]
    imagePullPolicy: Always
    env:
    - name: PROMETHEUS_IP
      value: prometheus.monitoring

  ```

6. Get the values for the custom metric on prometheus as a time series data

![image5](https://user-images.githubusercontent.com/83866176/149632411-9ec13769-36e4-427d-b9d5-1302842de14b.png)
   
7. Visualize the custom metric on hourly heatmap panel
   We can get the value for our custom metric by accessing it on grafana and selecting the visualization type to be ***Hourly Heatmap***. 
   To further customize and generalize our dashboard we can add variables to be able to filter and get different heatmaps for our  various clusters.

![image6](https://user-images.githubusercontent.com/83866176/149632486-670e53c0-b49a-4306-820d-e7fafd2ac59f.png)

## Further Scope

What we’ve done so far is to analyse the current time series data but what if we were able to predict when our instance will be down based on it’s past behaviour. That’s where machine learning and deep learning comes into picture. The scope is endless to come up with predictive algorithms to predict downtime and be ready with the preventive measures. I tried to train a day’s data for the metric `Disk WAL fsync duration` on the very famous state of the art model : **LSTM** which gave pretty good results. 
Furthermore, the research and implementation could be extended to models such as **ARENA** and then be incorporated into the system for better predictive alerting mechanisms.

![image4](https://user-images.githubusercontent.com/83866176/149632574-7c65ae82-cbe0-4a98-9207-5c5db13f25b3.png)
