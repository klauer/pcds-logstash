#!/bin/bash

echo "Reindexing TwinCAT events..."
. reindex.sh "^logstash-twincat-event-0-2.*" "twincat-event-0"
echo "Reindexing EPICS caPutLog events..."
. reindex.sh "^caputlog-event-0-2.*" "caputlog-event-0"
echo "Reindexing EPICS errlog events..."
. reindex.sh "^errlog-event-0-2.*" "errlog-event-0"

echo "Reindexing archiver appliance statistics..."
# This one's a mess (sorry!)
. reindex.sh "^archiver_appliance_metrics_.*" "archiver-appliance-stats" \
    "ctx._source.remove('lts_time_copy_data_into_store_percent'); \
    ctx._source.remove('lts_time_copy_data_into_store'); \
    ctx._source.remove('mts_time_copy_data_into_store_percent'); \
    ctx._source.remove('mts_time_copy_data_into_store'); \
    ctx._source.remove('sts_time_copy_data_into_store_percent'); \
    ctx._source.remove('sts_time_copy_data_into_store'); \
    ctx._source.remove('aggregated_appliance_event_rate_in_events_per_sec'); \
    ctx._source.remove('benchmark_writing_at_mb_per_sec'); \
    ctx._source.remove('data_rate_in_gb_per_year'); \
    "

echo "Reindexing Python events..."
. reindex.sh "^python-event-0-2.*" "python-event-0"
