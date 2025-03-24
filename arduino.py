import serial.tools.list_ports
import serial
import time

UNO = None

p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, A0, A1, A2, A3, A4, A5, A6, A7 = (
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21
)

class PINMODE():
	def __init__(self):
		self.input = 0
		self.input_pullup = 2
		self.output = 1
PINMODE = PINMODE()
IOModes = PINMODE
class ISR():
	def __init__(self):
		self.change = self.dual = self.both = 1
		self.falling = 2
		self.raising = 3
ISR = ISR()
interruptServiceRoutine = ISR

ISR_PINS = [
	[0, 0, 0],
	[0, 0, 0]
]


def connect():
	global UNO
	for item in [[a.hwid, a.device] for a in serial.tools.list_ports.comports()]:
		if "USB VID:PID=1A86:7523" in item[0]:
			UNO = serial.Serial(port=item[1], baudrate=2000000, timeout=1)
			if UNO.is_open:
				print("Connected to Arduino")
			break
	if UNO is None or not UNO.is_open:
		print("Failed to connect to Arduino")
	time.sleep(2)

def L32to8(value):
	return [value & 0xff, (value >> 8) & 0xff, (value >> 16) & 0xff, (value >> 24) & 0xff]

def B32to8(value):
	return list(reversed(L32to8(value)))

def OPbytes(*vals):
	return bytes(vals)

def uint_from_bytes(number, endian="little"):
	return sum([ord(num) << i * 8 for i, num in enumerate(reversed(number) if endian == "big" else number)])

def validate(val, obj):
	if val not in obj:
		raise ValueError(f"{val} not in {list(obj)}")

class pinMap:
	def __init__(self):
		self.analogPins = [3, 5, 6, 9, 10, 11, 14, 15, 16, 17, 18, 19]
		self.pins = [None for _ in self.analogPins]
		self.bindings = {}

	def write(self):
		import ctypes
		for b in self.bindings:
			pin = int(b)
			item = self.bindings[b]
			index = self.analogPins.index(pin)
			if index >= 0:
				self.pins[index] = ctypes.cast(item, ctypes.py_object).value

		for pin, value in zip(self.analogPins, self.pins):
			if value is not None:
				analogWrite(pin, value)

	def reset(self):
		self.pins = [None for _ in self.analogPins]

	def bind(self, index, variable):
		if index in self.analogPins:
			self.bindings[str(index)] = id(variable)
		else:
			raise ValueError(f"Invalid analog pin: {index}")

pinMap = pinMap()

def pinMode(pin, mode):
	validate(pin, range(2, 22))
	validate(mode, [0, 1, 2])
	if mode in [0, 1, 2]:
		UNO.write(OPbytes(0x00, pin, mode))

def digitalWrite(pin, value):
	validate(pin, range(2, 22))
	validate(value, range(0, 2))
	UNO.write(OPbytes(0x01, pin, value))

def digitalRead(pin):
	validate(pin, range(2, 22))
	UNO.write(OPbytes(0x02, pin))
	while UNO.in_waiting < 1:  # Ensure there's data available
		time.sleep(0.01)
	return not not ord(UNO.read(1))

def analogWrite(pin, value):
	validate(pin, [*list(range(14, 22)), 3, 5, 6, 9, 10, 11])
	validate(value, range(0, 256))
	UNO.write(OPbytes(0x03, pin, value))

def analogRead(pin):
	#validate(pin, range(14, 22))
	UNO.write(OPbytes(0x04, pin))
	while UNO.in_waiting < 2:  # Ensure there are 2 bytes available
		time.sleep(0.01)
	return uint_from_bytes([UNO.read(), UNO.read()], "big")

def readTrigger(triggerpin, triggervalue, readpin, waittime):
	validate(triggerpin, range(2, 22))
	validate(readpin, range(2, 22))
	validate(triggervalue, range(0, 256))
	waittime = int(waittime * 1000)
	UNO.timeout = waittime / 1000 + 1
	UNO.write(OPbytes(0x05, triggerpin, readpin, triggervalue, *L32to8(waittime)))
	while UNO.in_waiting < 2:  # Ensure 2 bytes for the result
		time.sleep(0.01)
	result = uint_from_bytes([UNO.read(), UNO.read()], "big")
	UNO.timeout = 1
	return result

def attachInterrupt(pin, pinMode, edge, timeout = 0):
	validate(pin, [2, 3])
	validate(edge, [1, 2, 3])
	validate(pinMode, [0, 2])
	UNO.write(OPbytes(0x06, 0x01, pin, (edge << 2) | pinMode, *L32to8(timeout)))

def detachInterrupt(pin, pinMode, edge, timeout = 0):
	validate(pin, [2, 3])
	validate(edge, [2, 3])
	validate(pinMode, [0, 2])
	UNO.write(OPbytes(0x06, 0x00, pin, (edge << 2) | pinMode))

def interrupts():
	UNO.write(OPbytes(0xff))
	while UNO.in_waiting < 2:
		time.sleep(0.01)
	dual_edge = [ord(UNO.read(1)) == 1, ord(UNO.read(1)) == 1]
	return [1 and dual_edge[0], 1 and dual_edge[1]]

servos = [0,0,0,0,0,0]
class Servo:
    def __init__(self, pin):
        global servos
        i = 0
        while i < len(servos):
            if servos[i] == 0:
                servos[i] = 1
                self.servo = i
                break
            i += 1
        else:
            raise ValueError("No available servo slots")
        
        self.pin = pin
        UNO.write(OPbytes(0x07, 0x00, self.servo, self.pin))  # Attach servo

    def write(self, val):
        validate(val, range(0, 181))  # Corrected range validation
        UNO.write(OPbytes(0x07, 0x02, self.servo, val))

    def detach(self):
        UNO.write(OPbytes(0x07, 0x01, self.servo))
        servos[self.servo] = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.detach()
