# ETCD Health Monitoring HeatMap
  ## 1. Introduction
  This document aims to explain and implement a visualization technique to monitor your containerized applications with the help of various tools and technologies. Too many buzzwords? Let's start with understanding each one in detail starting off with containerization. It's estimated that 90% of the applications in production will be containerized by the end of 2026, but what does it really mean? Containerization is a technique of bundling together our application with it's required libraries, configuration files, dependencies needed to run it so as to encapsulate the application as a single executable software package. This helps in virtualization of all resources and isolation of our application thus reducing overhead with enhanced portability. The first and still most popular container technology is `Docker`. Now, an average application in full blown production has a large number of these Docker containers each responsible for their individual fucntionalities and managing so many of them manually is not feasible. Hence `Kubernetes` comes into picture and serves as a container orchestration tool for automating deployment, scaling, etc with the help of a Master node and several Worker nodes. Worker nodes host the *pods* which basically are a collection of containers and the Master node manages the worker nodes. 

   ### 1.1 Meaning of the terms in title
   By now we have a fundamental understanding of how Kubernetes operates, so building onto that let's now figure out what do the terms in the title actually mean.
   
  `ETCD` is a crucial component of the Master node which is also called the *brain of Kubernetes* because it stores configuration information, state and metadata of clusters in a key-value pair database.
   
   Health of the ETCD put simply would be it's overall status. A slow ETCD would result in a slower Kubernetes and thus maintaining it is an important task.
   
   Monitoring involves getting insights into how the application behaves when deployed, gauging it's performance and removing bottlenecks.
   
   To consolidate all above, the tool that we shall be exploring to monitor the health of our ETCD is an `Hourly HeatMap`. HeatMaps are histogram representation over time with the bar height being replced with cells and color to represent different frequencies and values. To visulaize it better, the heatmap attached is the outcome of this document and we'll mainly be understanding and analysing the steps to build it. 
   
  ![hourly heatmap-etcd](https://user-images.githubusercontent.com/83866176/163716754-c6a261a5-1297-48b5-a326-ac307465ef80.png)
   
  ### 1.2 Technologies Used
 1. [Prometheus](https://prometheus.io/docs/introduction/overview/) is an open source systems monitoring solution with powerful metrics and efficient alerting mechanism. It collects and stores its metrics as time series data i.e metrics information is stored with the timestamp at which it was recorded. It can be accessed on port 9090 after successful installation.
 2. [Node Exporter](https://github.com/prometheus/node_exporter) is Prometheus’ metric exporter for OS and hardware metrics used primarily on unix systems (alternative for windows - windows exporter). It listens on port 9100.
 3. [Grafana](https://grafana.com/docs/) is a powerful visualization and analytics tool for time series data. We can access the time series data scrapped and stored by Prometheus and perform various transformations on them and analyse it on this platform.
 4. [Kubernetes](https://kubernetes.io/docs/home/) is a container orchestration tool that manages the deployment, up-scaling, down-scaling, etc of containerized applications.
 
   ### 1.3 Problem Statement 
  Firstly, why should such monitoring be required if Grafana provides developers with amusing graphs and visualizations of time series data? To answer that, let’s take an example to monitor ETCD within a kubernetes cluster. There can be multiple metric visualizations that represent anomalies or state of ETCD. Some of these may include the following:\
  a) `etcd_wal_fsync`\
  b) `etcd_db_fsync`\
  c) `etcd_file_descriptor`\
  d) `etcd_leader_election`\
  e) `etcd_client_traffic_in`\
  f) `etcd_database_size`\
  We will understand the relevance of each of them in the coming sections but for the time being, imagine the hassle of going through each graph and observing discrepancies, and over that, imagine having to do that for ‘n’ number of cluster instances. Therefore there is dire need for a one-stop solution to this problem. The heatmap visualization would culminate all of the above and just serve the purpose.
  
## 2. Approach Undertaken
The basic idea is to generate a custom metric which would be a weighted average of all the six essential metrics as mentioned in [section 1.3](#13-problem-statement). After we have the custom metric, let's say, *etcd_score*, we need to expose it using node exporter so that Prometheus is able to scrape it periodically. Grafana can then make use of the time series data of etcd_score and plot it using Hourly Heatmap visualization plugin. 
### 2.1 Selection of Metrics
It's only logical to choose metrics that depict changes and are correlated to the component being monitored, i.e. etcd, in this case. ETCD deals with read and write transactions of each and everything that's happening on the clusters, hence making database sync, size and network traffic oriented metrics more significant to moving forward with our approach.
- etcd_wal_fsync keeps track of Write Ahead Logs (WAL) 
- etcd_db_fsync
- etcd_database_size
- etcd_file_descriptor
- etcd_leader_election
- etcd_client_traffic_in
### 2.2 Need for weighted average