run:
	mkdir -p logs
	docker run --rm -it \
		-v ${PWD}/logs:/var/log/logstash \
		-v ${PWD}/../conf.d:/usr/share/logstash/pipeline/ \
		-v ${PWD}/output-testing.conf:/usr/share/logstash/pipeline/output-testing.conf \
		-p 7004:7004 \
		-p 7011:7011 \
		-p 54320:54320 \
		-p 54321:54321 \
		docker.elastic.co/logstash/logstash:7.7.1

.phony: run
