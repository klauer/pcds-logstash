pcds-logstash
=============

logstash configuration and round-trip testing for:

* PLC-generated JSON from [lcls-twincat-general](https://github.com/pcdshub/lcls-twincat-general).
* Python-generated JSON from [pcdsutils](https://github.com/pcdshub/pcdsutils/).
* caPutLog and errlog messages from miscellaneous IOCs (primarily [ads-ioc](https://github.com/pcdshub/ads-ioc/)).


Testing
=======

See [testing/](testing/README.md).

Schema / Indices
================

| Source   | Index Glob       | Schema example     |
|----------|------------------|--------------------|
| PLC      | twincat-event-*  |  twincat-event-0   |
| Python   | python-event-*   |  python-event-0    |
| caPutLog | caputlog-event-* |  caputlog-event-0  |
| errLog   | errlog-event-*   |  errlog-event-0    |
