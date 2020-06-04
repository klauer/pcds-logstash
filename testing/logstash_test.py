import contextlib
import json
import logging
import pprint
import socket

import pytest

try:
    import pcdsutils
    import pcdsutils.log
except ImportError:
    pcdsutils = None


logger = logging.getLogger(__name__)


LOG_HOST = 'localhost'
LOG_OUTPUT_SERVER = (LOG_HOST, 17771)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(('', 0))


@contextlib.contextmanager
def receive_from_logstash_output(max_length=8192):
    class Result:
        data = None

    with socket.create_connection(LOG_OUTPUT_SERVER) as output_sock:
        result = Result()
        yield result
        raw = output_sock.recv(max_length)

    logger.debug('Received %s', raw)
    result.data = json.loads(raw)
    print('Received:')
    pprint.pprint(result.data)


def send_and_receive(port, protocol, message):
    """Send message to (LOG_HOST, port) via protocol; receive logstash JSON."""
    if protocol == 'tcp' and not message.endswith('\n'):
        message = f'{message}\n'

    payload = message.encode('utf-8')
    logger.debug('Sending %s', payload)

    with receive_from_logstash_output() as received:
        dest = (LOG_HOST, port)
        if protocol == 'tcp':
            with socket.create_connection(dest) as log_sock:
                log_sock.send(payload)
        elif protocol == 'udp':
            udp_sock.sendto(payload, dest)
        else:
            raise ValueError('Bad protocol')

    return received.data


def log_and_receive(logger_func, *args, **kwargs):
    """Record Logger message and receive logstash JSON."""
    with receive_from_logstash_output() as received:
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
    'errlog': dict(
        protocol='tcp',
        port=7004,
    ),
    'caputlog': dict(
        protocol='tcp',
        port=7011,
    ),
    'plc_json': dict(
        protocol='udp',
        port=54321,
    ),
    'python_json_tcp': dict(
        protocol='tcp',
        port=54320,
    ),
    'python_json_udp': dict(
        protocol='udp',
        port=54320,
    ),
}

tests = [
    # -- error log tests --
    pytest.param(
        'errlog',
        'IOC=VonHamos01 sevr=major error log! IOC startup',
        {
            'log.iocname': 'VonHamos01',
            'log.severity': 'major',
            'log.message': 'error log! IOC startup',
         },
        id='errlog-major',
    ),

    pytest.param(
        'errlog',
        'IOC=VonHamos01 sevr=fatal fatal error message',
        {
            'log.iocname': 'VonHamos01',
            'log.severity': 'fatal',
            'log.message': 'fatal error message',
         },
        id='errlog-fatal',
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

    # -- plc JSON tests --
    pytest.param(
        'plc_json',
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

]

fail_tests = [
    # -- verifying check_vs_expected --
    pytest.param(
        'errlog',
        'IOC=VonHamos01 sevr=major error log! IOC startup',
        {'log.MISSING_KEY': 'VonHamos01'},
        ValueError,
        id='missing_key',
    ),

    pytest.param(
        'errlog',
        'IOC=VonHamos01 sevr=major error log! IOC startup',
        {'log.iocname': 'BAD_VALUE'},
        ValueError,
        id='bad_value',
    ),
]


@pytest.mark.parametrize('message_type, message, expected', tests)
def test_all(message_type, message, expected):
    info = message_types[message_type]
    result = send_and_receive(info['port'], info['protocol'], message)
    check_vs_expected(expected, result)


@pytest.mark.parametrize('message_type, message, expected, exc_class',
                         fail_tests)
def test_should_fail(message_type, message, expected, exc_class):
    info = message_types[message_type]
    result = send_and_receive(info['port'], info['protocol'], message)

    with pytest.raises(exc_class):
        check_vs_expected(expected, result)


@pytest.mark.parametrize(
    'python_message_type',
    [pytest.param('python_json_tcp', marks=pytest.mark.skip),
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

    result = log_and_receive(pcdsutils.log.logger.error, 'logger warning')
    pprint.pprint(result)

    expected = {
        'log.filename': 'logstash_test.py',
        'log.schema': f'python-event-{pcdsutils.log._LOGGER_SCHEMA_VERSION}',
        'log.msg': 'logger warning',
        'log.versions.pcdsutils': pcdsutils.__version__,
    }
    check_vs_expected(expected, result)
