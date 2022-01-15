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

#end_of_month = datetime.datetime.today().replace(day=1).date()

#last_day = end_of_month - datetime.timedelta(days=1)
#duration = '[1h]'

metrics = ['etcd_wal_fsync','etcd_db_fsync','etcd_file_descriptor','etcd_leader_election','etcd_client_traffic_in','etcd_database_size']


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

#print(etcd_wal_fsync, etcd_db_fsync, etcd_file_descriptor, etcd_leader_election, etcd_client_traffic_in, etcd_database_size)

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




#etcd_score = Decimal(wt_etcd_wal_fsync) * etcd_wal_fsync + Decimal(wt_etcd_db_fsync) * etcd_db_fsync + Decimal(wt_etcd_file_descriptor) * etcd_file_descriptor + Decimal(wt_etcd_leader_election) * etcd_leader_election + Decimal(wt_etcd_client_traffic_in) * etcd_client_traffic_in + Decimal(wt_etcd_database_size) * etcd_database_size


etcd_score = Decimal(wt_etcd_wal_fsync) * etcd_score_wal_fsync + Decimal(wt_etcd_db_fsync) * etcd_score_db_fsync + Decimal(wt_etcd_file_descriptor) * etcd_score_file_descriptor + Decimal(wt_etcd_leader_election) * etcd_score_leader_election + Decimal(wt_etcd_client_traffic_in) * etcd_score_client_traffic_in + Decimal(wt_etcd_database_size) * etcd_score_database_size

print('etcd_score',etcd_score)
