import contextlib
import json
import logging
import os
import pprint
import socket

import pytest

try:
    import pcdsutils
    import pcdsutils.log
except ImportError:
    pcdsutils = None


logger = logging.getLogger(__name__)


LOG_HOST = os.environ.get('TEST_OUTPUT_HOST', 'localhost')
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(('', 0))


@contextlib.contextmanager
def receive_from_logstash_output(port, max_length=8192):
    class Result:
        data = None

    with socket.create_connection((LOG_HOST, port)) as output_sock:
        result = Result()
        yield result
        raw = output_sock.recv(max_length)

    logger.debug('Received %s', raw)
    try:
        result.data = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Did not receive valid JSON from logstash: {raw}"
        )
    print('Received:')
    pprint.pprint(result.data)


def send_message(port, protocol, message):
    """Send message to (LOG_HOST, port) via `protocol`."""
    if protocol not in ('tcp', 'udp'):
        raise ValueError('Bad protocol')

    if protocol == 'tcp' and not message.endswith('\n'):
        message = f'{message}\n'

    payload = message.encode('utf-8')
    logger.debug('Sending %s', payload)

    dest = (LOG_HOST, port)
    if protocol == 'tcp':
        with socket.create_connection(dest) as log_sock:
            log_sock.send(payload)
    elif protocol == 'udp':
        udp_sock.sendto(payload, dest)


def send_by_type(message_type, message):
    """Send a message given the message type and message itself."""
    info = message_types[message_type]
    port = info['port']
    protocol = info['protocol']
    return send_message(port, protocol, message)


def send_and_receive(port, receive_port, protocol, message):
    """Send message to (LOG_HOST, port) via protocol; receive logstash JSON."""
    with receive_from_logstash_output(receive_port) as received:
        send_message(port, protocol, message)

    return received.data


def log_and_receive(receive_port, logger_func, *args, **kwargs):
    """Record Logger message and receive logstash JSON."""
    with receive_from_logstash_output(receive_port) as received:
        print('Calling', logger_func, 'with', args, kwargs)
        logger_func(*args, **kwargs)

    return received.data


def dotted_getitem(d, key):
    """Dotted getitem for dictionary `d` of `key`."""
    if '.' in key:
        key, remainder = key.split('.', 1)
        return dotted_getitem(d[key], remainder)

    return d[key]


def check_vs_expected(expected, received):
    """Check for some expected keys + values in the received dictionary."""
    errors = []
    for key, expected_value in expected.items():
        try:
            received_value = dotted_getitem(received, key)
        except KeyError:
            errors.append(f'Missing key {key!r}')
        else:
            try:
                assert received_value == expected_value
            except AssertionError as ex:
                # use pytest as a quick hack
                errors.append(f'Bad value for key {key!r}: {ex}')

    if errors:
        raise ValueError('\n' + '\n\n'.join(errors))


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

tests = [
    # -- error log tests --
    pytest.param(
        'epics_errlog',
        'IOC=VonHamos01 sevr=major error log! IOC startup',
        {
            'log.iocname': 'VonHamos01',
            'log.severity': 'major',
            'log.message': 'error log! IOC startup',
         },
        id='epics_errlog-major',
    ),

    pytest.param(
        'epics_errlog',
        'IOC=VonHamos01 sevr=fatal fatal error message',
        {
            'log.iocname': 'VonHamos01',
            'log.severity': 'fatal',
            'log.message': 'fatal error message',
         },
        id='epics_errlog-fatal',
    ),

    # -- caputlog tests --
    pytest.param(
        'caputlog',
        ('IOC=VonHamos01 03-Jun-20 17:03:29 ctl-logdev01 klauer '
         'CAPUTLOGTEST:VALUE new=0 old=1 min=0 max=1'),
        {
            'log.iocname': 'VonHamos01',
            'log.pvname': 'CAPUTLOGTEST:VALUE',
            'log.new_value': '0',
            'log.old_value': '1',
            'log.min_value': '0',
            'log.max_value': '1',
            'log.client_username': 'klauer',
            'log.client_hostname': 'ctl-logdev01',
            'log.timestamp': '2020-06-03T17:03:29.000Z',

        },
        id='caputlog_basic',
    ),

    pytest.param(
        'caputlog',
        ('IOC=VonHamos01 03-Jun-20 17:03:29 ctl-logdev01 klauer '
         'CAPUTLOGTEST:NEWVALUE new=0 old=1'),
        {
            'log.iocname': 'VonHamos01',
            'log.pvname': 'CAPUTLOGTEST:NEWVALUE',
            'log.new_value': '0',
            'log.old_value': '1',
            'log.client_username': 'klauer',
            'log.client_hostname': 'ctl-logdev01',
            'log.timestamp': '2020-06-03T17:03:29.000Z',

        },
        id='caputlog_no_minmax',
    ),

    pytest.param(
        'caputlog',
        ('03-Jun-20 17:03:29 ctl-logdev01 klauer '
         'CAPUTLOGTEST:NEWVALUE new=0 old=1'),
        {
            'log.pvname': 'CAPUTLOGTEST:NEWVALUE',
            'log.new_value': '0',
            'log.old_value': '1',
            'log.client_username': 'klauer',
            'log.client_hostname': 'ctl-logdev01',
            'log.timestamp': '2020-06-03T17:03:29.000Z',

        },
        id='caputlog_no_minmax_no_ioc',
    ),

    pytest.param(
        'caputlog',
        ('IOC=ioc-tc-mot-example 07-Jul-21 10:10:37 pscag06 root '
         'PLC:TST:MOT:SIM:01.SET new=Use old=Set'),
        {
            'log.iocname': 'ioc-tc-mot-example',
            'log.pvname': 'PLC:TST:MOT:SIM:01.SET',
            'log.new_value': 'Use',
            'log.old_value': 'Set',
            'log.client_username': 'root',
            'log.client_hostname': 'pscag06',
            'log.timestamp': '2021-07-07T10:10:37.000Z',

        },
        id='caputlog_enum',
    ),

    # -- plc JSON tests --
    pytest.param(
        'plc',
        '{"schema":"twincat-event-0","ts":1591288839.5965443,"plc":"PLC-LFE-VAC","severity":4,"id":0,"event_class":"97CF8247-B59C-4E2C-B4B0-7350D0471457","msg":"Critical (Pump time out.)","source":"plc_lfe_vac.plc_lfe_vac.GVL_Devices.IM1L0_XTES_PIP_01.fbLogger/Vacuum","event_type":3,"json":"{}"}',  # noqa
        {
            'log.event_class': '97CF8247-B59C-4E2C-B4B0-7350D0471457',
            'log.event_type': 3,
            'log.event_type_str': "message_sent",
            'log.function_block': "plc_lfe_vac.plc_lfe_vac.GVL_Devices.IM1L0_XTES_PIP_01.fbLogger",  # noqa
            'log.id': 0,
            'log.json': {},
            'log.msg': 'Critical (Pump time out.)',
            'log.plc': 'PLC-LFE-VAC',
            'log.schema': 'twincat-event-0',
            'log.severity': 4,
            'log.source': "plc_lfe_vac.plc_lfe_vac.GVL_Devices.IM1L0_XTES_PIP_01.fbLogger/Vacuum",  # noqa
            'log.subsystem': "Vacuum",
            'log.subsytem': "Vacuum",  # back-compat for typo
            'log.timestamp': "2020-06-04T16:40:39.596Z",
        },
        id='plc_vacuum',
    ),

    # -- gateway caputlog tests --
    pytest.param(
        'gateway_caputlog',
        'Nov 02 23:20:46 physics@opi15 XCS:USER:MCC:EPHOT:SET1 7351 old=7350',
        {
            'log.timestamp': '2022-11-02T23:20:46.000Z',  # 'Nov 02 23:20:46',
            'log.client_username': 'physics',
            'log.client_hostname': 'opi15',
            'log.pvname': 'XCS:USER:MCC:EPHOT:SET1',
            'log.new_value': '7351',
            'log.old_value': '7350',
            'log.iocname': '%{[path]}-gateway',  # unset because no path
        },
        id='gateway_caputlog',
    ),

]

fail_tests = [
    # -- verifying check_vs_expected --
    pytest.param(
        'epics_errlog',
        'IOC=VonHamos01 sevr=major error log! IOC startup',
        {'log.MISSING_KEY': 'VonHamos01'},
        ValueError,
        id='missing_key',
    ),

    pytest.param(
        'epics_errlog',
        'IOC=VonHamos01 sevr=major error log! IOC startup',
        {'log.iocname': 'BAD_VALUE'},
        ValueError,
        id='bad_value',
    ),
]


def check_timestamp(result):
    assert 'log' in result
    assert 'timestamp' in result['log']


@pytest.mark.parametrize('message_type, message, expected', tests)
def test_all(message_type, message, expected):
    info = message_types[message_type]
    result = send_and_receive(info['port'], info['receive_port'],
                              info['protocol'], message)
    check_vs_expected(expected, result)
    check_timestamp(result)


@pytest.mark.parametrize('message_type, message, expected, exc_class',
                         fail_tests)
def test_should_fail(message_type, message, expected, exc_class):
    info = message_types[message_type]
    result = send_and_receive(info['port'], info['receive_port'],
                              info['protocol'], message)

    with pytest.raises(exc_class):
        check_vs_expected(expected, result)


@pytest.mark.parametrize(
    'python_message_type',
    [pytest.param('python_json_tcp'),
     pytest.param('python_json_udp'),
     ]
)
def test_python_logging(python_message_type):
    if pcdsutils is None:
        pytest.skip('pcdsutils unavailable')

    info = message_types[python_message_type]
    pcdsutils.log.configure_pcds_logging(
        log_host=LOG_HOST,
        log_port=info['port'],
        protocol=info['protocol'],
    )

    result = log_and_receive(info['receive_port'], pcdsutils.log.logger.error,
                             'logger warning')
    pprint.pprint(result)

    expected = {
        'log.filename': 'logstash_test.py',
        'log.schema': f'python-event-{pcdsutils.log._LOGGER_SCHEMA_VERSION}',
        'log.msg': 'logger warning',
        'log.versions.pcdsutils': pcdsutils.__version__,
    }
    check_vs_expected(expected, result)
    check_timestamp(result)


@pytest.mark.parametrize(
    'python_message_type',
    [pytest.param('python_json_tcp'),
     pytest.param('python_json_udp'),
     ]
)
def test_python_logging_exceptions(python_message_type):
    if pcdsutils is None:
        pytest.skip('pcdsutils unavailable')

    info = message_types[python_message_type]
    pcdsutils.log.configure_pcds_logging(
        log_host=LOG_HOST,
        log_port=info['port'],
        protocol=info['protocol'],
    )

    def log_func():
        try:
            raise Exception('this is a an exception from the test suite')
        except Exception:
            pcdsutils.log.logger.exception('Caught an exception')
        import time
        time.sleep(10)

    result = log_and_receive(info['receive_port'], log_func)
    pprint.pprint(result)

    expected = {
        'log.filename': 'logstash_test.py',
        'log.schema': f'python-event-{pcdsutils.log._LOGGER_SCHEMA_VERSION}',
        'log.msg': 'Caught an exception',
        'log.versions.pcdsutils': pcdsutils.__version__,
    }
    check_vs_expected(expected, result)
    check_timestamp(result)
