#!/bin/bash

set -x

all_indices="logstash-twincat-event-0 caputlog-event-0 errlog-event-0 archiver-appliance-metrics python-event-0"

for idx in ${all_indices}; do
    echo "Initializing index: ${idx}"
    . initialize_index.sh "${idx}"
done

echo "All aliases:"
curl -s -XGET "$ES/_cat/aliases?format=json" |jq
