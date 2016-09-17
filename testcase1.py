import serial
import struct
import time

ser = serial.Serial(
                port ='/dev/ttyAMA0',
                baudrate = 115200,
                timeout = 3
)

def convertAndSend(number, numdigit):
        count = numdigit
        while (count > 0):
                count = count - 1
                if number>=255:
                        number = number - 255
                        ser.write(struct.pack('!B', 255))
                else:
                        ser.write(struct.pack('!B', number))
                        number = 0

ser.write("<")
ser.write(",")
# packet_seq
convertAndSend(1,1)
# component id
convertAndSend(245,1)
# packet data
convertAndSend(1111,8)
# crc
convertAndSend(0000,4)
ser.write(">")
