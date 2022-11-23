import pathlib
import shutil
import sys
import string

import logstash_test

config_path = pathlib.Path(sys.argv[1])
test_override_path = pathlib.Path(sys.argv[2])

with open("output-testing.conf", "rt") as f:
    template = string.Template(f.read())


for message_type, info in logstash_test.message_types.items():
    if message_type == "python_json_udp":
        continue
    if message_type == "python_json_tcp":
        message_type = "python"

    config = template.substitute(message_type=message_type, **info)
    path = config_path / message_type / "output-test.conf"
    print(f"* Writing {message_type} test config to {path}")
    with open(path, "wt") as f:
        print(config, file=f)

    elastic_configs = list(
        (config_path / message_type).glob("*output-elasticsearch*.conf")
    )
    for elastic_config in elastic_configs:
        print(f"  - Removing elasticsearch config for testing: {elastic_config}")
        elastic_config.unlink()

    for additional in (test_override_path / message_type).glob("*.conf"):
        print(
            f"  - Copying test-only config file override {message_type}/{additional.name}"
        )
        shutil.copy(additional, config_path / message_type / additional.name)
