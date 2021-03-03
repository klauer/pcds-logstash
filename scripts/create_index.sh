#!/bin/bash

ES=${ES:=localhost:9200}
INDEX=$1

# curl -s -XPUT $ES/_template/test-logs  -H 'Content-Type: application/json' -d'
# {
#   "template": "test-logs-*",
#   "settings": {
#     "number_of_shards": 10,
#     "number_of_replicas": 0,
#   },
# }
# '

set -x
curl -s -XDELETE $ES/test-logs*?pretty
curl -s -XDELETE $ES/_index_template/test-logs-template?pretty

curl -s -XPUT $ES/_index_template/test-logs-template?pretty  -H 'Content-Type: application/json' -d'
{
    "index_patterns": ["test-logs-*"],
    "template": {
        "settings": {
            "number_of_shards": 12,
            "number_of_replicas": 1
        },
        "aliases" : {
            "test-logs" : {}
        }
    },
    "version": 0,
    "_meta": {
        "description": "Index template"
    }
}
'

# curl -X POST "localhost:9200/_snapshot/my_backup/snapshot_1/_restore?pretty" -H 'Content-Type: application/json' -d'
# {
#   "indices": "data_stream_1,index_1,index_2",
#   "ignore_unavailable": true,
#   "include_global_state": false,              
#   "rename_pattern": "index_(.+)",
#   "rename_replacement": "restored_index_$1",
#   "include_aliases": false
# }
# '
# 
