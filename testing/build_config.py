import pathlib
import sys
import string

import logstash_test

config_path = pathlib.Path(sys.argv[1])

with open('output-testing.conf', 'rt') as f:
    template = string.Template(f.read())


for message_type, info in logstash_test.message_types.items():
    if message_type == 'python_json_udp':
        continue
    if message_type == 'python_json_tcp':
        message_type = 'python'

    config = template.substitute(message_type=message_type, **info)
    path = config_path / message_type / 'output-test.conf'
    print(f'* Writing {message_type} test config to {path}')
    with open(path, 'wt') as f:
        print(config, file=f)

    elastic_config = config_path / message_type / 'output-elasticsearch.conf'
    if elastic_config.exists():
        print('  - Removing elasticsearch config for testing')
        elastic_config.unlink()
