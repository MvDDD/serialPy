import serial.tools.list_ports
for item in [[a.hwid, a.device] for a in serial.tools.list_ports.comports()]:
	print(item)
	"""
	['USB VID:PID=1A86:7523 SER= LOCATION=1-1', 'COM10']
	['USB VID:PID=2341:0043 SER=95635333031351D0B0A2 LOCATION=1-1', 'COM6']
"""
