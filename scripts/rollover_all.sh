#!/bin/bash

set -euo pipefail

ES="localhost:9200"

rollover() {
  local target_idx="$1";
  curl -s -XPOST "$ES/$target_idx/_rollover?pretty=true" -H 'Content-Type: application/json' -d'
{
    "conditions": {
        "max_age": "30d",
        "max_size": "20G",
        "max_docs": 20000000
    }
}
'
}

export -f rollover

alias_list=$(curl -s -XGET "$ES/_cat/aliases" | cut -d' ' -f1 | grep -v ".kibana")

parallel rollover ::: $alias_list
