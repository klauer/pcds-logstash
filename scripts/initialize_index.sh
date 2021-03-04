#!/bin/bash

idx=$1

[[ -z "$idx" ]] && echo "initialize_index.sh index_name" && exit 1;

curl -s -XPUT "${ES}/_index_template/${idx}-template?pretty" -H 'Content-Type: application/json' -d'
{
    "index_patterns": ["'$idx'-*"],
    "template": {
        "settings": {
            "number_of_shards": 20,
            "number_of_replicas": 0
        }
    },
    "version": 0,
    "_meta": {
        "description": "'$idx' template"
    }
}
'

curl -s -XPUT "${ES}/${idx}-000001?pretty"
curl -s -XPUT "${ES}/${idx}-000001/_alias/${idx}?pretty"

