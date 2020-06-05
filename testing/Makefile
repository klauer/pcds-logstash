DOCKER_RUN_FLAGS ?= -i
PYTEST_FLAGS ?= -vv
PCDS_LOGSTASH_ROOT ?= ${PWD}/..
TEST_CONFIG_PATH = ${PWD}/.test_config/

TEST_OUTPUT_HOST ?= 127.0.0.1
TEST_OUTPUT_PORT_RANGE ?= 17771-17775
CAPUTLOG_PORT ?= 7011
ERRLOG_PORT ?= 7004
PYTHON_PORT ?= 54320
PLC_PORT ?= 54321

build_config:
	# a test configuration, removing elasticsearch output
	rm -rf ${TEST_CONFIG_PATH}
	cp -r ${PCDS_LOGSTASH_ROOT}/conf.d/ ${TEST_CONFIG_PATH}
	python build_config.py ${TEST_CONFIG_PATH}
	find ${TEST_CONFIG_PATH}

run: build_config
	mkdir -p logs
	docker run --rm $(DOCKER_RUN_FLAGS) -t \
		\
		-v ${PCDS_LOGSTASH_ROOT}/testing/logs:/var/log/logstash \
		-v ${PCDS_LOGSTASH_ROOT}/pipelines.yml:/usr/share/logstash/config/pipelines.yml \
		-v ${TEST_CONFIG_PATH}:/etc/logstash/conf.d \
		\
		-p $(TEST_OUTPUT_HOST):$(TEST_OUTPUT_PORT_RANGE):$(TEST_OUTPUT_PORT_RANGE)/tcp \
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

.PHONY: run test build_config
