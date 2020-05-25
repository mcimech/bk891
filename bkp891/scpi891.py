#-*- coding: utf-8
""" SCPI 'driver' for the BK Precision 891 LCR Meter

Requires pyserial 2.6 (2.5 might work) and Python 3.5 or greater.

MIT-Licensed: http://opensource.org/licenses/mit-license.html

Copyright 2020 Johannes Payr
johannes@arg-art.org
"""
from __future__ import print_function

import re
from enum import Enum
from time import sleep

import datetime

import serial
from serial.serialutil import SerialException


# TODO update constants
class MeasRange(Enum):
    HOLD = 0
    AUTO = 1


class MeasSpeed(Enum):
    SLOW = 1
    FAST = 2


class Measurement(Enum):
    CSQ = 0
    CSD = 1
    CSR = 2
    CPQ = 3
    CPD = 4
    CPR = 5
    CPG = 6
    LSQ = 7
    LSD = 8
    LSR = 9
    LPQ = 10
    LPD = 11
    LPR = 12
    LPG = 13
    ZTH = 14
    YTH = 15
    RX = 16
    GB = 17
    DCR = 18


MEASURES = frozenset(['L', 'C', 'R', 'Z'])
SECONDARY_MEASURES = frozenset(['D', 'Q', 'THETA', 'ESR'])


def connect(device, read_timeout=10, write_timeout=10, post_command_delay=150):
    """Connects to a specified device and, if successful, returns a
    ScpiConnection object."""

    try:
        con = serial.Serial(device, 9600, timeout=read_timeout,
                            writeTimeout=write_timeout)
    except SerialException as ex:
        if ex.errno == 16:
            print('Cannot open {0} - device is busy.'.format(device))
        raise
    return ScpiConnection(con, post_command_delay=post_command_delay)


def parse(cmd_result):
    """ Parses data returned from the device and returns it as an
    appropriate python datatype. """

    float_pattern = re.compile(
        r'^(\+|\-)[0-9]\.[0-9]{5,6}e(\-|\+)[0-9][0-9]')
    # cmd_result = cmd_result.decode('utf-8').replace('\r\n', '')
    cmd_result = cmd_result.replace('\r\n', '')
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
    """ Object handling all SCPI and IEEE 488 command I/O. """

    def __init__(self, con, post_command_delay):
        """ Accepts a pyserial Serial object and wraps it with python-ish
        SCPI functionality. """

        self.con = con
        self.post_command_delay = post_command_delay

    def close(self):
        """ Closes the connectiont to the device """
        self.con.close()

    def sendcmd(self, command):
        """ Sends a SCPI command to the device and returns the result in an
        appropriate python datatype.  Sleeps for the number of milliseconds
        specified by post_command_delay prior to reading the result.
        Note: This will insert the NL for you. """

        self.con.flushInput()
        self.con.flushOutput()

        result = None
        self.con.write('{0}{1}'.format(command, '\n').encode())

        # Pausing between commands so the meter doesn't error out when
        # other commands immediately follow.
        sleep(float(self.post_command_delay / 1000.0))
        self.con.flush()
        if command[-1] == '?':
            result = parse(self.con.readline().decode('utf-8'))

        return result

    # Calibrate Subsystem
    def calibrate(self, open_cal=True):
        """ Initialize calibration.

        If `open` is set to `True`, it starts the "open" calibration
        routine. Else, the "short" routine."""

        cmdstring = 'CALibrate:{0}'

        if open_cal:
            cmdstring.format('OPEN')
        else:
            cmdstring.format('SHORt')

        return self.sendcmd(cmdstring)

    def get_calibrate(self):
        """ Return calibration status.
        Return values
        `0`  Done
        `1`  Busy
        `-1` Fail """

        return self.sendcmd('CALibrate:BUSY?')

    # Bin Subsystem TODO

    # ...

    # Display Subsystem
    def set_displayfont(self, large=False):
        """ Set the display font to `large` or `normal`."""

        return self.sendcmd('DISPlay:FONT {0}'.format(int(large)))

    def get_displayfont(self):
        """ Return the display font.
        `0` Normal
        `1` Large"""

        return self.sendcmd('DISPlay:FONT?')

    def set_displaymode(self, scientific=False):
        """ Set the number display mode to "scientific" or "decimal" """

        return self.sendcmd('DISPlay:MODE {0}'.format(int(scientific)))

    def get_displaymode(self):
        """ Return the current display mode
        `0` Decimal
        `1` Scientific """

        return self.sendcmd('DISPlay:MODE?')

    def set_displaypage(self, page=0):
        try:
            page = int(page)
        except ValueError:
            raise ScpiException

        if (page < 0) or (page > 3):
            raise ScpiException

        return self.sendcmd('DISPlay:PAGE {0}'.format(page))

    def get_displaypage(self):
        """ Return display page
        `0` Bin
        `1` Measurement
        `2` Sweep
        `3` System """

        return self.sendcmd('DISPlay:PAGE?')

    # Fetch Subsystem
    def fetch(self):
        """ Returns the primary and secondary result currently measured
        from the device """

        return self.sendcmd('FETCh?')

    # Format Subsystem
    def set_format(self, binary=True):
        """ Set the number format to binary or ascii
        `True`  returns the binary (numbers only)
        `False` returns ascii format (with units) """

        return self.sendcmd('FORMat {0}'.format(int(binary)))

    def get_format(self):
        """ Return the number format (ASCii | REAL) """

        return self.sendcmd('FORMat?')

    # Frequency Subsystem
    def set_frequency(self, frequency):
        """ Sets the measurement frequency. """

        try:
            frequency = float(frequency)

        except ValueError:
            raise ScpiException

        if 20 > frequency or 300000 < frequency:
            raise ScpiException

        self.sendcmd('FREQuency {0}'.format(frequency))

    def get_frequency(self):
        """ Returns the current measurement frequency setting """

        return float(self.sendcmd('FREQuency?'))

    # Level Subsystem
    def set_aclevel(self, level=1.0):
        """ Set Signal test level
        Allowed values: 0.5 or 1.0 """
        try:
            level = float(level)

        except ValueError:
            raise ScpiException

        if (level != 0.5) and (level != 1.0):
            raise ScpiException

        return self.sendcmd('LEVel:AC {0}'.format(level))

    def get_aclevel(self):
        """ Return Signal test level """

        return self.sendcmd('LEVel:AC?')

    # Measurement Subsystem
    def set_function(self, funct=Measurement.RX):
        """ Set the measurement function.
        Use the enumeration bkp891.Measurement for values """

        return self.sendcmd('MEASurement:FUNCtion {0}'.format(funct.value))

    def get_function(self):
        """ Return the measurement function """

        return self.sendcmd('MEASurement:FUNCtion?')

    def set_speed(self, speed=MeasSpeed.SLOW):
        """ Set the measurement speed to fast or slow """

        return self.sendcmd('MEASurement:SPEED {0}'.format(speed.value))

    def get_speed(self):
        """ Return the measurement speed """

        return self.sendcmd('MEASurement:SPEED?')

    def set_measrange(self, range=MeasRange.AUTO):
        """ Set the measurement range to AUTO or HOLD """

        return self.sendcmd('MEASurement:RANGe {0}'.format(range.value))

    def get_measrange(self):
        """ Return the measurement range """

        return self.sendcmd('MEASurement:RANGe?')

    # Sweep Subsystem TODO

    # ...

    # Save Subsystem TODO

    # ...

    # System Subsystem
    def set_brightness(self, level):
        """ Set the screen brightness `(0-9)`"""

        try:
            level = int(level)
        except ValueError:
            raise ScpiException

        if (0 > level) or (9 < level):
            raise ScpiException

        return self.sendcmd('SYStem:BRIGhtness {0}'.format(level))

    def get_brightness(self):
        """ Return the screen brightness """

        return self.sendcmd('SYStem:BRIGhtness?')

    def set_beeper(self, on=True):
        """ Set the beeper """

        if on:
            return self.sendcmd('SYStem:BEEPer ON')
        return self.sendcmd('SYStem:BEEPer OFF')

    def get_beeper(self):
        """ Return the state of the beeper """

        return self.sendcmd('SYStem:BEEPer?')

    def set_date(self, isodate=''):
        """ Set the date from a date string in the format YYYY-MM-DD.
        Default sets the date to today """

        dt = datetime.date.today()
        if isodate != '':
            try:
                dt = datetime.date.fromisoformat(isodate)
            except ValueError:
                raise ScpiException

        return self.sendcmd('SYStem:DATE {0},{1},{2}'.format(dt.year,
                                                             dt.month,
                                                             dt.day))

    def get_date(self):
        """ Return the instrument date """

        return self.sendcmd('SYStem:DATE?')

    def set_time(self, isotime=''):
        """ Set the time from a date string in the format HH:MM:SS.
            Default sets the time to now """

        dt = datetime.datetime.now().time()
        if isotime != '':
            try:
                dt = datetime.time.fromisoformat(isotime)
            except ValueError:
                raise ScpiException

        return self.sendcmd('SYStem:TIME {0},{1},{2}'.format(dt.hour,
                                                             dt.minute,
                                                             dt.second))

    def get_time(self):
        """ Return the instrument time """

        return self.sendcmd('SYStem:TIME?')

    def get_error(self):
        """ Return the first element of the error stack """

        return self.sendcmd('SYStem:ERRor?')

    # TODO add IP subsubsystem

    # IEEE 488.2 commands
    def get_instrument(self):
        """ Queries and returns the instrument ID
        containing the model, firmware version, and serial number. """

        return self.sendcmd('*IDN?')

    def clear_instrument(self):
        """ Send the *CLS command to the instrument. """

        return self.sendcmd('*CLS')

    def reset(self):
        """ Reset the instrument. """

        return self.sendcmd('*RST')

    def save_configuration(self, number=1):
        """ Save the current configuration to memory """

        try:
            number = int(number)

        except ValueError:
            raise ScpiException

        return self.sendcmd('*SAV {0}'.format(number))

    def recall_configuration(self, number=1):
        """ Recall a configuration from memory """

        try:
            number = int(number)

        except ValueError:
            raise ScpiException

        return self.sendcmd('*RCL {0}'.format(number))


class ScpiException(Exception):
    """ Exception class for SCPI Commands. Raised when an enum-bounded
    parameter is invalid """

    pass
