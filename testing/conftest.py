message_types = {
    'epics_errlog': dict(
        protocol='tcp',
        port=7004,            # <-- this is the port logstash expects errlog on
        receive_port=17771,   # <-- this is the port we configure logstash to send us info
    ),
    'caputlog': dict(
        protocol='tcp',
        port=7011,
        receive_port=17772,
    ),
    'plc': dict(
        protocol='udp',
        # port=54321,  # <-- NOTE: this goes to the UDP tee process (on prod)
        port=54322,  # <-- NOTE: this goes directly to logstash
        receive_port=17773,
    ),
    'python_json_tcp': dict(
        protocol='tcp',
        port=54320,
        receive_port=17774,
    ),
    'python_json_udp': dict(
        protocol='udp',
        port=54320,
        receive_port=17774,
    ),
    'gateway_caputlog': dict(
        protocol='tcp',
        port=17775,
        receive_port=17776,
    ),
}
