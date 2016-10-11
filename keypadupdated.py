import RPi.GPIO as GPIO
import time
import os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

MATRIX = [
	[1,2,3],
	[4,5,6],
	[7,8,9],
	["*",0,"#"]
	]

ROW = [18,23,24,25]
COL = [4,17,22]
node = ''
start = ''
end = ''
state = 0

print state

os.system('flite -t "Enter, start, destination." ')

for j in range(3):
	GPIO.setup(COL[j], GPIO.OUT)
	GPIO.output(COL[j], 1)

for i in range(4):
	GPIO.setup(ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
	while(True):
		for j in range(3):
			GPIO.output(COL[j], 0)

			for i in range(4):
				if GPIO.input(ROW[i]) == 0:
					if i == 0:
						if j == 0:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 1
							node += str(number)
						if j == 1:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 2
							node += str(number)
						if j == 2:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 3
							node += str(number)
					elif i == 1:
						if j == 0:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 4
							node += str(number)
						if j == 1:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 5
							node += str(number)
						if j == 2:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 6
							node += str(number)
					elif i == 2:
						if j == 0:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 7
							node += str(number)
						if j == 1:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 8
							node += str(number)
						if j == 2:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 9
							node += str(number)
					elif i == 3:
						if j == 1:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							number = 0
							node += str(number)
						if j == 0:
							if len(node) == 2:
								while(GPIO.input(ROW[i]) == 0):
									pass
								time.sleep(0.1)
								print node
								if state == 0:
									start=node
									print start
									os.system("flite -t 'Start, destination, is, "+node+" ' ")
									node=''
									state=1
									print state
									os.system('flite -t "Enter, end, destination." ')
								if state == 1:
								if state == 1:
									if len(node) == 2:
										end = node
										print end
										os.system("flite -t 'End, destination, is, "+node+" ' ")
										node=''
										os.system('flite -t "Entering, navigation, mode." ')
						if j == 2:
							while(GPIO.input(ROW[i]) == 0):
								pass
							time.sleep(0.1)
							node=''
							os.system('flite -t "Re-enter, destination." ')
					if len(node) == 2:
						print node
						#os.system("flite -voice slt -t 'Your, start, destination, is, "+node+" ' ")
						if state == 0:
							os.system("flite -t 'Start, destination, is, "+node+" ' ")
						if state == 1:
							os.system("flite -t 'End, destination, is, "+node+" ' ")
						os.system('flite -t "To, confirm, press, *." ')
						os.system('flite -t "To, re-enter, destination, press, #." ')
						time.sleep(0.25)

			GPIO.output(COL[j], 1)

except KeyboardInterrupt:
	GPIO.cleanup()


