DOCKER_RUN_FLAGS ?= -i
PYTEST_FLAGS ?= -vv
PCDS_LOGSTASH_ROOT ?= ${PWD}/..

TEST_OUTPUT_HOST ?= 127.0.0.1
TEST_OUTPUT_PORT ?= 17771
CAPUTLOG_PORT ?= 7011
ERRLOG_PORT ?= 7004
PYTHON_PORT ?= 54320
PLC_PORT ?= 54321

run:
	mkdir -p logs
	docker run --rm $(DOCKER_RUN_FLAGS) -t \
		\
		-v ${PWD}/logs:/var/log/logstash \
		-v ${PCDS_LOGSTASH_ROOT}/pipelines.yml:/usr/share/logstash/pipelines.yml \
		-v ${PCDS_LOGSTASH_ROOT}/conf.d:/etc/logstash/conf.d \
		-v ${PWD}/output-testing.conf:/etc/logstash/conf.d/output-elasticsearch.conf \
		\
		-p $(TEST_OUTPUT_HOST):$(TEST_OUTPUT_PORT):$(TEST_OUTPUT_PORT)/tcp \
		-p $(TEST_OUTPUT_HOST):$(ERRLOG_PORT):$(ERRLOG_PORT)/tcp \
		-p $(TEST_OUTPUT_HOST):$(CAPUTLOG_PORT):$(CAPUTLOG_PORT)/tcp \
		-p $(TEST_OUTPUT_HOST):$(PYTHON_PORT):$(PYTHON_PORT)/udp \
		-p $(TEST_OUTPUT_HOST):$(PLC_PORT):$(PLC_PORT)/udp \
		\
		docker.elastic.co/logstash/logstash:7.7.1
	# TODO:
	# -p $(TEST_OUTPUT_HOST):$(PYTHON_PORT):$(PYTHON_PORT)/tcp

test:
	TEST_OUTPUT_PORT=$(TEST_OUTPUT_PORT) python -m pytest \
		$(PYTEST_FLAGS) logstash_test.py

.phony: run test
