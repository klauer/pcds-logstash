#!/bin/bash

set -x

ES=${ES:=localhost:9200}
source_idx_match=$1
target_idx=$2
script=$3
source_indices=$(
    curl -s -XGET "$ES/_cat/indices?format=json" | 
    jq '[.[] | select(.index|test("'${source_idx_match}'")) | .index] | sort'
)

[[ -z "$source_idx_match" || -z "$target_idx" ]] && echo "reindex.sh source_idx_match target_idx" && exit 1;
[[ "$source_indices" == "[]" ]] && echo "No matching source indices?" && exit 1;

echo "Source index regex: $source_idx_match"
echo "Target index alias: $target_idx"
echo "Found matching indices: $source_indices"

. initialize_index.sh "$target_idx"

echo "Reindexing matching indices -> '$target_idx'..."

if [ ! -z "$script" ]; then
    curl -s -XPOST "${ES}"'/_reindex?wait_for_completion=true&require_alias=true&pretty=true' -H 'Content-Type: application/json' -d'
{
    "source": {
        "index": '"$source_indices"'
    },
    "dest": {
        "index": "'$target_idx'"
    },
    "conflicts": "proceed",
    "script": {
        "source": "'"$script"'",
        "lang": "painless"
    } 
}
'
else
    curl -s -XPOST "${ES}"'/_reindex?wait_for_completion=true&require_alias=true&pretty=true' -H 'Content-Type: application/json' -d'
{
    "source": {
        "index": '"$source_indices"'
    },
    "dest": {
        "index": "'$target_idx'"
    },
    "conflicts": "proceed"
}
'
fi

# conflicts only in archiver appliance data :(

. rollover.sh "$target_idx"

echo "New index document count:"
. sum_document_count.sh "$target_idx-0.*"
echo "Old index document count:"
. sum_document_count.sh "$target_idx-2.*"
