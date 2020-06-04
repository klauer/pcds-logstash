import json
import logging
import pprint
import socket

import pytest


logger = logging.getLogger(__name__)

LOG_HOST = 'localhost'
LOG_OUTPUT_SERVER = (LOG_HOST, 17771)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(('', 0))

def send_and_receive(port, protocol, message):
    """Send message to (LOG_HOST, port) via protocol; receive logstash JSON."""
    if protocol == 'tcp' and not message.endswith('\n'):
        message = f'{message}\n'

    payload = message.encode('utf-8')
    logger.debug('Sending %s', payload)
    dest = (LOG_HOST, port)
    with socket.create_connection(LOG_OUTPUT_SERVER) as output_sock:
        if protocol == 'tcp':
            with socket.create_connection(dest) as log_sock:
                log_sock.send(payload)
        elif protocol == 'udp':
            udp_sock.sendto(payload, dest)
        else:
            raise ValueError('Bad protocol')

        raw = output_sock.recv(8192)
        logger.debug('Received %s', raw)
        json_dict = json.loads(raw)
        print('Received:')
        pprint.pprint(json_dict)
        return json_dict


def dotted_getitem(d, key):
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
    'python_json': dict(
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
        id='basic errlog',
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

    # -- plc JSON tests --
    pytest.param(
        'plc_json',
        '{"schema":"twincat-event-0","ts":1591288839.5965443,"plc":"PLC-LFE-VAC","severity":4,"id":0,"event_class":"97CF8247-B59C-4E2C-B4B0-7350D0471457","msg":"Critical (Pump time out.)","source":"plc_lfe_vac.plc_lfe_vac.GVL_Devices.IM1L0_XTES_PIP_01.fbLogger/Vacuum","event_type":3,"json":"{}"}',
        {
            'log.event_class': '97CF8247-B59C-4E2C-B4B0-7350D0471457',
            'log.event_type': 3,
            'log.event_type_str': "message_sent",
            'log.function_block': "plc_lfe_vac.plc_lfe_vac.GVL_Devices.IM1L0_XTES_PIP_01.fbLogger",
            'log.id': 0,
            'log.json': {},
            'log.msg': 'Critical (Pump time out.)',
            'log.plc': 'PLC-LFE-VAC',
            'log.schema': 'twincat-event-0',
            'log.severity': 4,
            'log.source': "plc_lfe_vac.plc_lfe_vac.GVL_Devices.IM1L0_XTES_PIP_01.fbLogger/Vacuum",
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
