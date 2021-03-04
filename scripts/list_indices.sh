#!/bin/bash

ES=${ES:=localhost:9200}
MATCH=$1

curl -s -XGET "$ES/_cat/indices?format=json" | jq '[.[] | select(.index|test("'${MATCH}'")) | .index] | sort'
