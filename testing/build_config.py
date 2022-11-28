import pathlib
import shutil
import sys
import string

import logstash_test

config_path = pathlib.Path(sys.argv[1])
test_override_path = pathlib.Path(sys.argv[2])

for message_type, info in logstash_test.message_types.items():
    if message_type == "python_json_udp":
        continue
    if message_type == "python_json_tcp":
        message_type = "python"

    print(f"Message type: {message_type}")

    # Use config_for_tests/*.conf as templates for *all* configs
    for template_fn in test_override_path.glob("*.conf"):
        with open(template_fn, "rt") as f:
            template = string.Template(f.read())

        config = template.substitute(message_type=message_type, **info)
        path = config_path / message_type / template_fn.name
        print(f"  - Writing test config {template_fn.name} to {path}")
        with open(path, "wt") as f:
            print(config, file=f)

    # Remove elasticsearch configs as we don't have a database for testing
    elastic_configs = list(
        (config_path / message_type).glob("*output-elasticsearch*.conf")
    )
    for elastic_config in elastic_configs:
        print(f"  - Removing elasticsearch config for testing: {elastic_config}")
        elastic_config.unlink()

    # And finally, add on "override" configurations that do something special for
    # test purposes only
    for additional in (test_override_path / message_type).glob("*.conf"):
        print(
            f"  - Copying test-only config file override {message_type}/{additional.name}"
        )
        shutil.copy(additional, config_path / message_type / additional.name)

    print()
