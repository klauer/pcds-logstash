#!/bin/bash

ES=${ES:=localhost:9200}
target_idx=$1

curl -s -XPOST "$ES/$target_idx/_rollover?pretty=true" -H 'Content-Type: application/json' -d'
{
    "conditions": {
        "max_age": "30d",
        "max_size": "20G",
        "max_docs": 20000000
    }
}
'
