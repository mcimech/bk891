bkp879b.py
===========

bkp879b.py is a self-contained SCPI "driver" library for the BK Precision 879B and 878B LCR Meters. It provides a pythonic interface to all of the documented SCPI commands in the manual.  Query results are returned as native python datatypes for easy integration into the rest of your project.

Serial communication is handled by the pyserial library (http://pyserial.sourceforge.net/)

- Comma-separated results are contained inside a tuple
- All scientific notation values are returned as floats
- 'ON' 'OFF' values are returned as a boolean
- Integer values are returned as integers
- N or '----' values are returned as a None type
- Everything else is returned as a utf-8 string

For a detailed list of functionality see the bkp879b.py file

Usage:

	import bkp879b

	instrument = bkp879b.connect("/dev/yourdevice") # Windows users can just pass in 'COMx'

	instrument.set_primary("C") # Sets primary measurement to Capacitence
	instrument.set_secondary("ESR") # Sets secondary measurement to equivalent series resistance

	# Activate auto-fetching mode on the meter by pressing "USB" Key
	for reading in instrument.auto_fetch():
		print(reading)


Dependencies
===========
pyserial >= 2.6


Contributing
===========
Fork and submit a pull request.

