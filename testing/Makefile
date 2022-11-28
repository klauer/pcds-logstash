DOCKER_RUN_FLAGS ?= -i
PYTEST_FLAGS ?= -vv
PCDS_LOGSTASH_ROOT ?= ${PWD}/..
TEST_CONFIG_PATH = ${PWD}/.test_config/
TEST_OVERRIDE_PATH = ${PWD}/config_for_tests/
PYTEST_TIMEOUT ?= "5.0"

TEST_OUTPUT_HOST ?= 127.0.0.1
TEST_OUTPUT_PORT_RANGE ?= 17771-17776
CAPUTLOG_PORT ?= 7011
GATEWAY_CAPUTLOG_PORT ?= 54330
ERRLOG_PORT ?= 7004
PYTHON_PORT ?= 54320
UDP_PORT_RANGE ?= 54320-54329

build_config:
	# a test configuration, removing elasticsearch output
	rm -rf ${TEST_CONFIG_PATH}
	cp -r ${PCDS_LOGSTASH_ROOT}/conf.d/ ${TEST_CONFIG_PATH}
	python build_config.py "${TEST_CONFIG_PATH}" "${TEST_OVERRIDE_PATH}"
	find ${TEST_CONFIG_PATH}
	mkdir -p logs
	chmod 0777 logs

run: build_config
	docker run --rm $(DOCKER_RUN_FLAGS) -t \
		\
		-v ${PCDS_LOGSTASH_ROOT}/testing/logs:/var/log/logstash \
		-v ${PCDS_LOGSTASH_ROOT}/pipelines.yml:/usr/share/logstash/config/pipelines.yml \
		-v ${TEST_CONFIG_PATH}:/etc/logstash/conf.d \
		\
		-p $(TEST_OUTPUT_HOST):$(TEST_OUTPUT_PORT_RANGE):$(TEST_OUTPUT_PORT_RANGE)/tcp \
		-p $(TEST_OUTPUT_HOST):$(ERRLOG_PORT):$(ERRLOG_PORT)/tcp \
		-p $(TEST_OUTPUT_HOST):$(CAPUTLOG_PORT):$(CAPUTLOG_PORT)/tcp \
		-p $(TEST_OUTPUT_HOST):$(GATEWAY_CAPUTLOG_PORT):$(GATEWAY_CAPUTLOG_PORT)/tcp \
		-p $(TEST_OUTPUT_HOST):$(UDP_PORT_RANGE):$(UDP_PORT_RANGE)/udp \
		-p $(TEST_OUTPUT_HOST):$(PYTHON_PORT):$(PYTHON_PORT)/tcp \
		\
		docker.elastic.co/logstash/logstash:7.17.7

compose-test: build_config
	docker-compose up \
			--abort-on-container-exit \
			--exit-code-from pytest

test:
	PYTEST_TIMEOUT=$(PYTEST_TIMEOUT) \
		 python -m pytest $(PYTEST_FLAGS) logstash_test.py

.PHONY: run test build_config compose-test
