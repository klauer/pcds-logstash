Logstash testing
----------------

Testing using a docker container and some pytest-based tests, which round-trip:

    Python log message -> logstash input -> logstash JSON output -> Python

Docker
------

```sh
$ make run
```

Test
----

```sh
$ make test
```
