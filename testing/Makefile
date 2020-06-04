DOCKER_RUN_FLAGS ?= -i
PYTEST_FLAGS ?= -vv

run:
	mkdir -p logs
	docker run --rm $(DOCKER_RUN_FLAGS) -t \
		-v ${PWD}/logs:/var/log/logstash \
		-v ${PWD}/../conf.d:/usr/share/logstash/pipeline/ \
		-v ${PWD}/output-testing.conf:/usr/share/logstash/pipeline/output-elasticsearch.conf \
		-p 17771:17771 \
		-p 7004:7004 \
		-p 7011:7011 \
		-p 54320:54320/tcp -p 54320:54320/udp \
		-p 54321:54321/udp \
		docker.elastic.co/logstash/logstash:7.7.1

test:
	pytest $(PYTEST_FLAGS) logstash_test.py

.phony: run test
