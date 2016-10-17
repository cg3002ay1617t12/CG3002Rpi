from enum import Enum
from audio import tts
import RPi.GPIO as GPIO
import time, os, signal, json

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class State(Enum):
	START   = 0
	START_1 = 1
	START_2 = 2
	END     = 3
	END_1   = 4
	END_2   = 5
	FFA     = 6

class Transitions(Enum):
	KEY_DIGIT = 0
	KEY_HASH  = 1
	KEY_STAR  = 2
	KEY_INCR  = 3
	KEY_DECR  = 4

class KEY(object):
	"""Contains GPIO -> value mapping"""
	MAP = {
		(25,22) : 1,
		(25,17) : 2,
		(25,4)  : 3,
		(24,22) : 4,
		(24,17) : 5,
		(24,4)  : 6,
		(23,22) : 7,
		(23,17) : 8,
		(23,4)  : 9,
		(18,22) : '*',
		(18,17) : 0,
		(18,4)  : '#'
	}
	def __init__(self, ports):
		"""Takes a GPIO port_id and returns a KEY object with transition types and value"""
		self.value = KEY.MAP[ports]
		self.types = []
		if self.value in [1,2,3,4,5,6,7,8,9,0]:
			self.types.append(Transitions.KEY_DIGIT)
		if self.value == 8:
			self.types.append(Transitions.KEY_DECR)
		if self.value == 2:
			self.types.append(Transitions.KEY_INCR)
		if self.value == '*':
			self.types.append(Transitions.KEY_STAR)
		if self.value == '#':
			self.types.append(Transitions.KEY_HASH)

class Action(Enum):
	APPEND        = 1
	CLEAR         = 2
	CONFIRM_START = 3
	CONFIRM_END   = 4
	NULL          = 5
	QUIT          = 6
	INCR          = 7
	DECR          = 8

State.transitions = {
	State.START : {
		Transitions.KEY_DIGIT : (State.START_1, Action.APPEND),
		Transitions.KEY_HASH : (State.START, Action.CLEAR)
	},
	State.START_1 : {
		Transitions.KEY_DIGIT : (State.START_2, Action.APPEND),
		Transitions.KEY_HASH : (State.START, Action.CLEAR)
	},
	State.START_2 : {
		Transitions.KEY_STAR : (State.END, Action.CONFIRM_START),
		Transitions.KEY_HASH : (State.END, Action.CLEAR)
	},
	State.END : {
		Transitions.KEY_DIGIT : (State.END_1, Action.APPEND),
		Transitions.KEY_HASH : (State.END, Action.CLEAR)
	},
	State.END_1 : {
		Transitions.KEY_DIGIT : (State.END_2, Action.APPEND),
		Transitions.KEY_HASH : (State.END, Action.CLEAR)
	},
	State.END_2 : {
		Transitions.KEY_HASH : (State.END, Action.CLEAR),
		Transitions.KEY_HASH : (State.FFA, Action.CONFIRM_END)
	},
	State.FFA : {
		Transitions.KEY_INCR : (State.FFA, Action.INCR),
		Transitions.KEY_DECR : (State.FFA, Action.DECR),
		Transitions.KEY_STAR : (State.START, Action.NULL),
		Transitions.KEY_STAR : (State.FFA, Action.QUIT)
	}
}

PROMPTS = {
	Transitions.KEY_HASH : "to re-enter, press hash",
	Transitions.KEY_STAR : "to confirm, press star",
	Transitions.KEY_INCR : "",
	Transitions.KEY_DECR : "",
	Transitions.KEY_DIGIT : "please enter a digit",
}

AFFIRMS = {
	Action.APPEND: "you have entered %s",
	Action.CLEAR : "cleared all input",
	Action.CONFIRM_START : "your start destination is %s",
	Action.CONFIRM_END : "your end destination is %s",
	Action.NULL : "",
	Action.QUIT : "Shutting down"
}

ENV                = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
EVENT_PIPE         = ENV["EVENT_PIPE"]
PID                = ENV["PID_FILE"]

# if not os.path.exists(EVENT_PIPE):
	# os.mkfifo(EVENT_PIPE)

# pipe_out = os.open(EVENT_PIPE, os.O_WRONLY)
# fpid     = open(PID, 'r')
# pid      = fpid.read()

node = ''
start = ''
end = ''
state = State.START
send = ''
# MATRIX = [
# 	[1,2,3],    (25,22), (25,17), (25,4)
# 	[4,5,6],    (24,22), (24,17), (24,4)
# 	[7,8,9],    (23,22), (23,17), (23,4)
# 	["*",0,"#"] (18,22), (18,17), (18,4)
# 	]
ROW = [18,23,24,25] # G, H, J, K
COL = [4,17,22] # D, E, F
def action_on_transit(val, action):
	""" Do something upon transition to next state ONCE"""
	global send
	print("Action : "),
	print(action)
	# Issue prompts for all the transitions in current state
	for transition in State.transitions[state]:
		tts(PROMPTS[transition])
	
	if action is Action.APPEND:
		tts(AFFIRMS[action], (val,))
		send += str(val)
	elif action is Action.CLEAR:
		tts(AFFIRMS[action])
		send = ''
	elif action is Action.CONFIRM_START:
		tts(AFFIRMS[action], (send,))
		# os.write(pipe_out, send + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.CONFIRM_END:
		tts(AFFIRMS[action], (send,))
		# os.write(pipe_out, send + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.QUIT:
		# os.write(pipe_out, "q" + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.NULL:
		pass
	else:
		raise Exception("Unrecognized action!")

def handler(key):
	# Construct key object
	print("Key triggered : %s" % str(key.value))
	global state
	for transition in key.types:
		try:
			(state, action) = State.transitions[state][transition]
			action_on_transit(key.value, action)
		except KeyError as e:
			pass

def setup():
	for j in COL:
		GPIO.setup(j, GPIO.OUT)
		GPIO.output(j, 1)

	for i in ROW:
		GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main():
	MATRIX = {
		18 : {
			4 : False,
			17 : False,
			22 : False
		},
		23 : {
			4 : False,
			17: False,
			22: False
		},
		24 : {
			4 : False,
			17: False,
			22: False
		},
		25 : {
			4 : False,
			17: False,
			22: False
		}
	}
	key_down = False
	setup()
	try:
		while(True):
			for j in COL:
				GPIO.output(j, 0)
				for i in ROW:
					if (GPIO.input(i) == 0):
						if not MATRIX[i][j]:
							key_down = True
							time.sleep(0.1)
							key = KEY((i, j))
							handler(key)
						else:
							# Key is already pressed
							pass
					else:
						MATRIX[i][j] = False
						pass
				GPIO.output(j, 1)
	except KeyboardInterrupt as e:
		GPIO.cleanup()

	# try:
	# 	while(True):
	# 		for j in COL:
	# 			GPIO.output(j, 0)
	# 			for i in row:
	# 				if GPIO.input(i) == 0:
	# 					if i == 0:
	# 						if j == 0:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 1
	# 							node += str(number)
	# 						if j == 1:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 2
	# 							node += str(number)
	# 						if j == 2:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 3
	# 							node += str(number)
	# 					elif i == 1:
	# 						if j == 0:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 4
	# 							node += str(number)
	# 						if j == 1:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 5
	# 							node += str(number)
	# 						if j == 2:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 6
	# 							node += str(number)
	# 					elif i == 2:
	# 						if j == 0:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 7
	# 							node += str(number)
	# 						if j == 1:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 8
	# 							node += str(number)
	# 						if j == 2:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 9
	# 							node += str(number)
	# 					elif i == 3:
	# 						if j == 1:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							number = 0
	# 							node += str(number)
	# 						if j == 0:
	# 							if len(node) == 2:
	# 								while(GPIO.input(ROW[i]) == 0):
	# 									pass
	# 								time.sleep(0.1)
	# 								print node
	# 								if state == 0:
	# 									start=node
	# 									print start
	# 									os.system("flite -t 'Start, destination, is, "+node+" ' ")
	# 									node=''
	# 									state=1
	# 									print state
	# 									os.system('flite -t "Enter, end, destination." ')
	# 								if state == 1:
	# 									if len(node) == 2:
	# 										end = node
	# 										print end
	# 										os.system("flite -t 'End, destination, is, "+node+" ' ")
	# 										node=''
	# 										os.system('flite -t "Entering, navigation, mode." ')
	# 						if j == 2:
	# 							while(GPIO.input(ROW[i]) == 0):
	# 								pass
	# 							time.sleep(0.1)
	# 							node=''
	# 							os.system('flite -t "Re-enter, destination." ')
	# 					if len(node) == 2:
	# 						print node
	# 						#os.system("flite -voice slt -t 'Your, start, destination, is, "+node+" ' ")
	# 						if state == 0:
	# 							os.system("flite -t 'Start, destination, is, "+node+" ' ")
	# 						if state == 1:
	# 							os.system("flite -t 'End, destination, is, "+node+" ' ")
	# 						os.system('flite -t "To, confirm, press, *." ')
	# 						os.system('flite -t "To, re-enter, destination, press, #." ')
	# 						time.sleep(0.25)

	# 			GPIO.output(COL[j], 1)
	# except KeyboardInterrupt:
	# 	GPIO.cleanup()

if __name__ == "__main__":
	main()