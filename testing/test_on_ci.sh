#!/bin/bash


SCRIPT_PATH=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
cd "${SCRIPT_PATH}" || exit 1

if [[ $(docker ps -q) != "" ]]; then
  echo -e "\n* Containers already running? Sorry, this script is not very smart.";
  exit 1;
fi

echo -e "\n* Starting up logstash in docker..."
DOCKER_RUN_FLAGS=--detach make run

echo -e "\n* Installing test dependencies..."
python -m pip install --upgrade pip
python -m pip install --requirement requirements.txt

echo -e "\n* Running containers:"
docker ps

echo -e "\n* Network configuration:"
/sbin/ifconfig

echo -e "\n* Waiting for logstash..."
# ... but also wait for logstash to get started. It's slow.
until docker logs "$(docker ps -q)" |grep "Starting tcp input"; do sleep 1; done
echo -e "\n* logstash appears ready."; sleep 15

timeout 100 make test
EXIT_CODE=$?

echo -e "\n* After the test run, 'docker ps' reports:"
docker ps

echo -e "\n* Logstash logs:"
tail -n 100 "logs/*.log"

echo -e "\n* Docker logs:"
docker logs "$(docker ps -q)"

echo -e "\n* Stopping docker containers..."
docker stop "$(docker ps -q)"

exit $EXIT_CODE
