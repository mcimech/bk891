#-*- coding: utf-8
''' SCPI 'driver' for the BK Precision 879B LCR Meter
Should also work with the 878B.

Requires pyserial 2.6 (2.5 might work) and Python 2.6 or greater.
Compatible with Python 3.x as well.

MIT-Licensed: http://opensource.org/licenses/mit-license.html

Copyright 2012 Jim Battin
jrbattin@gmail.com
'''
from __future__ import print_function

import re
from time import sleep

import serial
from serial.serialutil import SerialException


FREQUENCIES = frozenset([100, 120, 1000, 10000])
MEASURES = frozenset(['L', 'C', 'R', 'Z'])
SECONDARY_MEASURES = frozenset(['D', 'Q', 'THETA', 'ESR'])
TOLERANCES = frozenset([1, 5, 10, 20])


def connect(device, read_timeout=10, write_timeout=10, post_command_delay=150):
    '''Connects to a specified device and, if successful, returns a
    ScpiConnection object.'''

    try:
        con = serial.Serial(device, 9600, timeout=read_timeout, writeTimeout=write_timeout)
    except SerialException as ex:
        if ex.errno == 16:
            print('Cannot open {0} - device is busy.'.format(device))
        raise
    return ScpiConnection(con, post_command_delay=post_command_delay)


def parse(cmd_result):
    ''' Parses data returned from the device and returns it as an
    appropriate python datatype. '''

    float_pattern = re.compile(r'^(\+|\-)[0-9]\.[0-9]{5,6}e(\-|\+)[0-9][0-9]')
    cmd_result = cmd_result.decode('utf-8').replace('\r\n', '')
    split_input = cmd_result.split(',')
    result = []

    for data in split_input:
        if data == 'N' or data.startswith('----'):
            result.append(None)

        elif re.match(float_pattern, data):
            result.append(float(data))

        elif data == 'ON':
            result.append(True)

        elif data == 'OFF':
            result.append(False)

        else:
            try:
                result.append(int(data))

            except ValueError:
                result.append(data)

    if len(result) == 1:
        return result[0]

    return tuple(result)


class ScpiConnection(object):
    ''' Object handling all SCPI and IEEE 488 command I/O. '''

    def __init__(self, con, post_command_delay):
        ''' Accepts a pyserial Serial object and wraps it with python-ish SCPI
        functionality. '''

        self.con = con
        self.post_command_delay = post_command_delay

    def close(self):
        ''' Closes the connectiont to the device '''
        self.con.close()

    def sendcmd(self, command):
        ''' Sends a SCPI command to the device and returns the result in an
        appropriate python datatype.  Sleeps for the number of milliseconds
        specified by post_command_delay prior to reading the result.
        Note: This will insert the NL for you. '''

        self.con.flushInput()
        self.con.flushOutput()

        result = None
        self.con.write('{0}{1}'.format(command, '\n'))

        # Pausing between commands so the meter doesn't error out when
        # other commands immediately follow.
        sleep(float(self.post_command_delay / 1000.0))
        self.con.flush()
        if command[-1] == '?':
            result = parse(self.con.readline().decode('utf-8'))

        return result

    def auto_fetch(self, quantity=0):
        ''' A generator yielding a result tuple containing the primary,
        secondary, and compared result with each iteration.

        Set the optional parameter 'quantity' to the maximnum number
        of samples you wish to collect (default is 0: unlimited)

        Note: will yield a None if there is a timeout waiting for a
        reading. '''

        self.con.flushInput()
        self.con.flushOutput()
        counter = 0

        while True:
            result = parse(self.con.readline())

            if len(result) == 0:
                yield None
            else:
                counter += 1
                yield result

            if quantity is not 0 and quantity == counter:
                return

    # 'Fetch Subsystem' - Fetches reading
    def fetch(self):
        ''' Returns the primary, secondary, and tolerance compared
        result currently measured from the device

        Returns a tuple containing the primary value (float), secondary
        value (float), and the tolerance compared (integer or None). '''

        return self.sendcmd('FETCh?')

    # Frequency Subsystem
    def set_frequency(self, frequency):
        ''' Sets the measurment frequency.  Accepted values are:
        100, 120, 1000, and 10000. '''

        frequency = int(frequency)
        if frequency not in FREQUENCIES:
            raise ScpiException('''Valid frequencies are: 100, 120, 1000,
                and 10000.''')

        self.sendcmd('FREQuency {0}'.format(frequency))

    def get_frequency(self):
        ''' Returns the current measurement frequency setting
        returns a string of '100Hz', '120Hz', '1kHz', or '10kHz' '''

        return self.sendcmd('FREQuency?')

    # Function Subsystem
    def set_primary(self, param):
        ''' Sets the primary measurement parameter.  Accepts a string
        value of 'L', 'C', 'R', or 'Z'.

        L: Inductance
        C: Capacitance
        R: Resistance
        Z: Impedance '''

        param = param.upper()

        if param not in MEASURES:
            raise ScpiException('''Valid primary parameters are 'L', 'C', 'R',
                or 'Z'.''')

        self.sendcmd('FUNCtion:impa {0}'.format(param.upper()))

    def set_secondary(self, param):
        ''' Sets the secondary measurement parameter.  Accepts a string
        value of 'D', 'Q', 'THETA', or 'ESR'

        D: Dissipation factor
        Q: Quality factor
        THETA: Phase angle (Labeled as 'θ' on the meter)
        ESR: Equivalent series resistance. '''

        param = param.upper()
        if param not in SECONDARY_MEASURES:
            raise ScpiException('''Valid secondary parameters are 'D',
            'Q', 'THETA', or 'ESR' ''')

        self.sendcmd('FUNCtion:impb {0}'.format(param.upper()))

    def get_primary(self):
        ''' Queries and returns the primary measurement parameter
        as a string.  Returns 'L', 'C', 'R', or 'Z'.

        L: Inductance
        C: Capacitance
        R: Resistance
        Z: Impedance '''

        return self.sendcmd('FUNCtion: impa?')

    def get_secondary(self):
        ''' Queries and returns the secondary measurement parameter
        as a string.  Retrusn 'D', 'Q', 'THETA', or 'ESR'

        D: Dissipation factor
        Q: Quality factor
        THETA: Phase angle (Labeled as 'θ' on the meter)
        ESR: Equivalent series resistance. '''

        return self.sendcmd('FUNCtion: impb?')

    def set_equiv_series(self):
        ''' Sets measurement mode to series. '''
        self.sendcmd('FUNCtion:EQUivalent SERies')

    def set_equiv_parallel(self):
        ''' Sets measurement mode to parallel. '''

        self.sendcmd('FUNCtion:EQUivalent parallel')

    def get_equiv(self):
        ''' Queries and returns the measurement mode (series or parallel)

        returns a string of 'SER' or 'PAL'. '''
        return self.sendcmd('FUNCtion:EQUivalent?')

    # Calculate Subsystem
    def set_relative(self, relative_value):
        ''' Enabels or disables relative function based on
        boolean value. '''

        if relative_value:
            self.sendcmd('CALCulate:RELative:STATe ON')
        else:
            self.sendcmd('CALCulate:RELative:STATe OFF')

    def get_relative_state(self):
        ''' Queries and returns the state of the relative function
        Returns a boolean value of the current relative state. '''
        return self.sendcmd('CALCulate:RELative:STATe?')

    def get_relative_value(self):
        ''' Queries and returns the relative value or None if unavailable
        Returns a float of the relative offset or None if Relative state
        is inactive. '''
        return self.sendcmd('CALCulate:RELative:VALUe?')

    def set_tolerance_state(self, tolerance_state):
        ''' Enables or disables tolerance state based on boolean value. '''
        if tolerance_state:
            self.sendcmd('CALCulate:TOLerance:STATe ON')
        else:
            self.sendcmd('CALCulate:TOLerance:STATe OFF')

    def set_tolerance_range(self, tolerance_range):
        ''' Sets the current tolerance range to 1, 5, 10, or 20 percent. '''
        if tolerance_range not in TOLERANCES:
            raise ScpiException(''' Valid tolerance ranges are 1, 5,
                10 or 20. ''')

        self.sendcmd('CALCulate:TOLerance:RANGe {0}'.format(tolerance_range))

    def get_tolerance_state(self):
        ''' Queries and returns whether tolerance is enabled or disabled
        Returns a boolean value. '''
        return self.sendcmd('CALCulate:TOLerance:STATe?')

    def get_tolerance_nominal(self):
        ''' Queries and returns the nominal value fo tolerance or None
        if unavailable. Returns a float value or None if unavailable. '''
        return self.sendcmd('CALCulate:TOLerance:NOMinal?')

    def get_tolerance_value(self):
        ''' Queries and returns the percent value of tolerance or None
        if unavailable.  Returns a float value or None if unavailable. '''
        return self.sendcmd('CALCulate:TOLerance:VALUe?')

    def get_tolerance_range(self):
        ''' Queries and returns the tolerance range.
        Returns a string value of 'BIN1', 'BIN2', 'BIN3', 'BIN4'
        or None if unavailable. '''
        return self.sendcmd('CALCulate:TOLerance:RANGe?')

    def set_recording_state(self, recording_state):
        ''' Enables or disables the recording state of the device. '''

        if recording_state:
            self.sendcmd('CALCulate:RECording:STATe ON')
        else:
            self.sendcmd('CALCulate:RECording:STATe OFF')

    def get_recording_state(self):
        ''' Queries and returns the status of recording.
        Returns a boolean value. '''
        return self.sendcmd('CALCulate:RECording:STATe?')

    def get_recording_max(self):
        ''' Queries and returns the max recorded value. Returns a tuple of
        floats containing the primary and secondary maximum measurement. '''
        return self.sendcmd('CALCulate:RECording:MAXimum?')

    def get_recording_min(self):
        ''' Queries and returns the minimum recorded value. Returns a tuple of
        floats containing the primary and secondary minimum measurement. '''
        return self.sendcmd('CALCulate:RECording:MINimum?')

    def get_recording_avg(self):
        ''' Queries and returns the average recorded value. Returns a tuple of
        floats containing the primary and secondary average measurement. '''
        return self.sendcmd('CALCulate:RECording:AVERage?')

    def get_recording_present(self):
        ''' Queries and returns the present value of the recording function.
        Returns a tuple of floats containing the primary and secondary present
        measurement. '''
        return self.sendcmd('CALCulate:RECording:PRESent?')

    # IEEE 488 commands
    def local_lockout(self):
        ''' Locks the front panel '''
        self.sendcmd('*LLO')

    def go_local(self):
        ''' Puts the meter into local state - clears front-panel lockout. '''
        self.sendcmd('*GLO')

    def get_instrument(self):
        ''' Queries and returns the instrument ID
        containing the model, firmware version, and serial number. '''

        return self.sendcmd('*IDN?')


class ScpiException(Exception):
    ''' Exception class for SCPI Commands. Raised when an enum-bounded
    parameter is invalid '''

    pass

