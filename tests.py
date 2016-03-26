''' Unit tests for bkp879b.py '''
from __future__ import print_function

import unittest
import bkp879b
from serial import SerialException


def dummy_sendcmd(command):
    ''' Dummy sendcmd method for testing SCPI command generation '''
    return '{0}\n'.format(command)


class TestConnect(unittest.TestCase):
    ''' Test cases for the connect function '''

    def setUp(self):
        ''' Test setup '''
        self.bkp = bkp879b
        self.goodserial = '/dev/tty.SLAB_USBtoUART'
        self.badserial = '/dev/null'

    def test_goodconnect(self):
        ''' Test to ensure our 'happy path' of a valid serial connection.
            Assumes self.goodserial is set to a valid serial device '''

        try:
            scpi_obj = self.bkp.connect(self.goodserial)
        except SerialException:
            print('\n!!!!!!! IMPORTANT !!!!!!!!\n',
                  'Skipped test: test_goodconnect because no device found\n'
                  '!!!!!!! IMPORTANT !!!!!!!!')
            return

        self.assertTrue(isinstance(scpi_obj, bkp879b.ScpiConnection))

    def test_badconnect(self):
        ''' Test to ensure our 'unhappy path' is producing the correct
            exception. Assumes self.badserial is set to an invalid
            serial device. '''
        with self.assertRaises(SerialException):
            self.bkp.connect(self.badserial)


class TestParse(unittest.TestCase):
    ''' Test cases for the parse function '''

    def setUp(self):
        ''' Test setup '''
        self.bkp = bkp879b

    def test_integers(self):
        ''' Tests integer parsing '''
        ints = self.bkp.parse(b'+800,-900234,0,27'.encode('ascii'))
        self.assertTupleEqual(ints, (800, -900234, 0, 27))

    def test_floats(self):
        ''' Tests float parsing '''
        floats = self.bkp.parse('+2.345678e+04,-1.34567e-01'.encode('ascii'))
        self.assertTupleEqual(floats, (23456.78, -0.134567))

    def test_booleans(self):
        ''' Tests boolean parsing '''
        bools = self.bkp.parse('ON,OFF'.encode('ascii'))
        self.assertTupleEqual(bools, (True, False))

    def test_literals(self):
        ''' Tests string literal parsing '''
        literals = self.bkp.parse('HOLD,TESTING'.encode('ascii'))
        self.assertTupleEqual(literals, ('HOLD', 'TESTING'))

    def test_blanks(self):
        ''' Tests blank '----' results '''
        blanks = self.bkp.parse('----,N'.encode('ascii'))
        self.assertTupleEqual(blanks, (None, None))

    def test_single(self):
        ''' Tests non-tuple single result '''

        single_int = self.bkp.parse('123'.encode('ascii'))
        single_float = self.bkp.parse('+2.345678e+04'.encode('ascii'))
        single_none = self.bkp.parse('N'.encode('ascii'))
        single_bool = self.bkp.parse('ON'.encode('ascii'))
        single_literal = self.bkp.parse('HOLD'.encode('ascii'))

        self.assertTupleEqual(
            (single_int, single_float, single_none, single_bool, single_literal),
            (123, 23456.78, None, True, 'HOLD')
        )


class TestScpiConnection(unittest.TestCase):
    ''' Tests SCPI Connection object - specifically the command output '''

    def setUp(self):
        ''' Sets up our ScpiConnection object with sendcmd dummy object '''
        self.scpi = bkp879b.ScpiConnection(None, 100)
        self.scpi.sendcmd = dummy_sendcmd

    def test_badfrequency(self):
        ''' Ensures appropriate exception is thrown for set_frequency. '''

        with self.assertRaises(bkp879b.ScpiException):
            self.scpi.set_frequency(90)

    def test_badprimary(self):
        ''' Ensures appropriate exception is thrown for set_primary. '''

        with self.assertRaises(bkp879b.ScpiException):
            self.scpi.set_primary('THETA')

    def test_badsecondary(self):
        ''' Ensures appropriate exception is thrown for set_primary. '''

        with self.assertRaises(bkp879b.ScpiException):
            self.scpi.set_secondary('L')

    def test_badtolerance(self):
        ''' Ensures appropriate exception is thrown for
        set_tolerance_range. '''

        with self.assertRaises(bkp879b.ScpiException):
            self.scpi.set_tolerance_range(3)


if __name__ == '__main__':
    unittest.main()
