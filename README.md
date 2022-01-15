# Heatmap to monitor ETCD health
Here, in this document I try to explain the steps and technologies behind coming up with an etcd-monitoring heatmap which could help anyone to predict if the system/cluster is healthy just by looking at the colors on heatmap, with green indicating good and red indicating bad health respectively. 
![hourly heatmap-etcd](https://user-images.githubusercontent.com/83866176/149630777-46792f3d-e084-4791-b686-44465310ceba.png)

The technologies used are : `Prometheus`, `Node Exporter`, `Grafana` and `Kubernetes`.

1. [Prometheus](https://prometheus.io/docs/introduction/overview/) is an open source systems monitoring solution with powerful metrics and efficient alerting mechanism. It collects and stores its metrics as time series data i.e metrics information is stored with the timestamp at which it was recorded. It can be accessed on port 9090 after successful installation. 
2. [Node Exporter](https://github.com/prometheus/node_exporter) is Prometheus’ metric exporter for OS and hardware metrics used primarily on unix systems (alternative for windows - windows exporter). It listens on port 9100.
3. [Grafana](https://grafana.com/docs/) is a powerful visualization and analytics tool for time series data. We can access the time series data scrapped and stored by Prometheus and perform various transformations on them and analyse it on this platform.
4. [Kubernetes](https://kubernetes.io/docs/home/) is a container orchestration tool that manages the deployment, up-scaling, down-scaling, etc of containerized applications. 

## Why is it required?

Firstly, why should such monitoring be required if Grafana provides developers with amusing graphs and visualizations of time series data? To answer that, let’s take an example to monitor ETCD within a kubernetes cluster. The basic metrics one would go for would be : Client Traffic in, Leader elections,etc. Imagine the hassle of going through each graph and observing discrepancies, and over that, imagine having to do that for ‘n’ number of cluster instances. The heatmap visualization would culminate all of the above and more to provide developers and testers with one stop destination to monitor their clusters. 

## Steps to build the heatmap
1. Configure your system/instance with prometheus and enable node exporter. ([click here](https://netcorecloud.com/tutorials/setup-prometheus-and-exporters/) to follow the installation guide)
2. Install and configure grafana ([click here](https://grafana.com/docs/grafana/latest/installation/debian/) for installation steps)
3. Install Hourly heatmap plugin on grafana
   Hourly heatmap aggregates data into buckets of day and hour to analyse activity or traffic during the day. It can easily be installed in a few steps. 
   [Click Here](https://grafana.com/grafana/plugins/marcusolsson-hourly-heatmap-panel/?tab=installation) to go to the website for installation guide. 
   Once installed, it should be visible on your Grafana port right away under different types of visualizations. 
   
   ![image1](https://user-images.githubusercontent.com/83866176/149631560-5564ba48-38ec-4b75-a31e-8ebd426a3d0f.png)
4. Build a docker image to get custom metrics from your kubernetes cluster.
   
   *Dockerfile image* : bejoyr/heatmapvsoc:v3
   
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
   - Python file ```heatmap.py``` to generate custom metrics for node exporter to expose 
     
   
  The working is explained in the figure below and can be understood by observing the flow. The python file parses the configuration file to get the weights of the different metrics used for our monitoring. It then establishes a connection with the prometheus server which listens on port 9090 to get the values of metrics at that instant. The metric values then undergo a series of computational steps involving checking for thresholds to get the final etcd_score which is written into a special file(\*.prom) which would be used by node exporter to expose the custom metric value on its port from where prometheus can scrape it. This needs to be set up in a ***crontab*** fashion of events for the metric to insert data into the textfile-collector at regular intervals of time so that we get a time series data that can be visualized on grafana.
  (to enable textfile collector for custom metric we need to start node exporter with --collector.textfile.directory flag and set it equal to the special \*.prom file path)

  ![image2](https://user-images.githubusercontent.com/83866176/149632085-d73cb9c0-9738-424e-beee-7fc167116349.png)

   
5. Configure the image into a pod on your kubernetes cluster using the dokcker image name : ``bejoyr/heatmapvsoc:v3``
   
   We need to set this pod to run it's contents at regular intervals of time, we can do that by setting an argument in our yaml configuration file
   ```
   spec:
     container:
     -name : <INSERT NAME>
        args: ["-c", "while true ; do  python3 heatmap.py > <INSERT PATH TO *.prom FILE> ; sleep 15; done"]
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
