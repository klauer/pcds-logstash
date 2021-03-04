#!/bin/bash

set -x

ES=${ES:=localhost:9200}
idx_match=$1

echo "(Index regex: ${idx_match})"
curl -s -XGET "$ES/_cat/indices?format=json" | \
    jq '[.[] | select(.index|test("'${idx_match}'")) | ."docs.count" | tonumber] | add'
