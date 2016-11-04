from enum import Enum
from audio import tts
import RPi.GPIO as GPIO
import time, os, signal, json, shlex, subprocess, threading
from threading import Thread

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
NUM_WORKERS = 1

class State(Enum):
	MAP_BUILDING         = 0
	MAP_BUILDING_CONFIRM = 1
	MAP_LEVEL            = 2
	MAP_LEVEL_CONFIRM    = 3
	START                = 4
	START_1              = 5
	START_2              = 6
	END                  = 7
	END_1                = 8
	END_2                = 9
	FFA                  = 10

class Transitions(Enum):
	KEY_DIGIT = 0
	KEY_HASH  = 1
	KEY_STAR  = 2
	KEY_INCR  = 3
	KEY_DECR  = 4
	KEY_MUSIC = 5
	KEY_NAV   = 6
	KEY_MAP   = 7
	KEY_INSTR = 8
	KEY_PREV  = 9
	KEY_REACHED   = 10
	KEY_STEP_OFF = 11
	KEY_STEP_ON  = 12

# MATRIX = [
# 	[1,2,3],    (25,22), (25,17), (25,4)
# 	[4,5,6],    (24,22), (24,17), (24,4)
# 	[7,8,9],    (23,22), (23,17), (23,4)
# 	["*",0,"#"] (18,22), (18,17), (18,4)
# 	]
ROW = [18,23,24,25] # G, H, J, K
COL = [4,17,22] # D, E, F

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
		(18,22) : '#',
		(18,17) : 0,
		(18,4)  : '*'
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
		if self.value == 5:
			self.types.append(Transitions.KEY_MUSIC)
			self.types.append(Transitions.KEY_NAV)
		if self.value == '*':
			self.types.append(Transitions.KEY_STAR)
		if self.value == '#':
			self.types.append(Transitions.KEY_HASH)
		if self.value == 0:
			self.types.append(Transitions.KEY_INSTR)
		if self.value == 4:
			self.types.append(Transitions.KEY_PREV)
		if self.value == 6:
			self.types.append(Transitions.KEY_REACHED)
		if self.value == 1:
			self.types.append(Transitions.KEY_STEP_OFF)
		if self.value == 3:
			self.types.append(Transitions.KEY_STEP_ON)

class Action(Enum):
	START            = 1
	APPEND           = 2
	CLEAR            = 3
	CONFIRM_START    = 4
	CONFIRM_END      = 5
	NULL             = 6
	QUIT             = 7
	INCR             = 8
	DECR             = 9
	PLAY_MUSIC       = 10
	NAV              = 11
	CONFIRM_BUILDING = 12
	CONFIRM_LEVEL    = 13
	DOWNLOAD_MAP     = 14
	GET_INSTR        = 15
	GET_PREV         = 16
	REACHED          = 17
	STEP_OFF         = 18
	STEP_ON          = 19

State.transitions = {
	State.MAP_BUILDING  : {
		Transitions.KEY_DIGIT : (State.MAP_BUILDING_CONFIRM, Action.APPEND),
		Transitions.KEY_HASH  : (State.MAP_BUILDING, Action.CLEAR)
	},
	State.MAP_BUILDING_CONFIRM  : {
		Transitions.KEY_DIGIT : (State.MAP_BUILDING_CONFIRM, Action.APPEND),
		Transitions.KEY_HASH  : (State.MAP_BUILDING, Action.CLEAR),
		Transitions.KEY_STAR  : (State.MAP_LEVEL, Action.CONFIRM_BUILDING)
	},
	State.MAP_LEVEL : {
		Transitions.KEY_DIGIT : (State.MAP_LEVEL_CONFIRM, Action.APPEND),
		Transitions.KEY_HASH  : (State.MAP_LEVEL, Action.CLEAR)
	},
	State.MAP_LEVEL_CONFIRM : {
		Transitions.KEY_DIGIT : (State.MAP_LEVEL_CONFIRM, Action.APPEND),
		Transitions.KEY_STAR : (State.START, Action.CONFIRM_LEVEL),
		Transitions.KEY_HASH  : (State.MAP_LEVEL, Action.CLEAR)
	},
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
		Transitions.KEY_HASH : (State.START, Action.CLEAR)
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
		Transitions.KEY_STAR : (State.FFA, Action.CONFIRM_END),
		Transitions.KEY_HASH : (State.END, Action.CLEAR)
	},
	State.FFA : {
		Transitions.KEY_INCR : (State.FFA, Action.INCR),
		Transitions.KEY_DECR : (State.FFA, Action.DECR),
		Transitions.KEY_NAV  : (State.FFA, Action.NAV),
		Transitions.KEY_STAR  : (State.MAP_BUILDING, Action.DOWNLOAD_MAP),
		Transitions.KEY_HASH : (State.START, Action.START),
		Transitions.KEY_INSTR : (State.FFA, Action.GET_INSTR),
		Transitions.KEY_PREV : (State.FFA, Action.GET_PREV),
		Transitions.KEY_REACHED : (State.FFA, Action.REACHED),
		Transitions.KEY_STEP_ON : (State.FFA, Action.STEP_ON),
		Transitions.KEY_STEP_OFF : (State.FFA, Action.STEP_OFF)
		# Transitions.KEY_STAR : (State.FFA, Action.QUIT)
		# Transitions.KEY_MUSIC : (State.FFA, Action.PLAY_MUSIC)
	}
}

PROMPTS = {
	Transitions.KEY_DIGIT : "Please enter a digit",
	Transitions.KEY_HASH  : "To re-enter, press hash",
	Transitions.KEY_STAR  : "To confirm, press star",
	Transitions.KEY_INCR  : "Press 2 to increment step",
	Transitions.KEY_DECR  : "Press 8 to decrement step",
	Transitions.KEY_MUSIC : "If you are bored of my voice, press 5 to play a song"
}

AFFIRMS = {
	Action.START: "Please enter a new start destination",
	Action.APPEND: "you have entered %s",
	Action.CLEAR : "cleared all input",
	Action.CONFIRM_START : "your start destination is %s",
	Action.CONFIRM_END : "your end destination is %s",
	Action.CONFIRM_BUILDING : "your building is COM %s",
	Action.CONFIRM_LEVEL : "your level is %s",
	Action.NULL : "",
	Action.QUIT : "Shutting down",
	Action.NAV : "",
	Action.DOWNLOAD_MAP : "",
	Action.GET_INSTR : "",
	Action.GET_PREV : "",
	Action.REACHED : "You have shot harem bay",
	Action.STEP_OFF : "You have turned off step counter",
	Action.STEP_ON : "You have turned on step counter"
}

ALLOWED_BUILDINGS  = [1,2]
ALLOWED_LEVELS     = [1,2]
ENV                = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
EVENT_PIPE         = ENV["EVENT_PIPE"]
PID                = ENV["PID_FILE"]

if not os.path.exists(EVENT_PIPE):
	os.mkfifo(EVENT_PIPE)

pipe_out = os.open(EVENT_PIPE, os.O_WRONLY)
fpid     = open(PID, 'r')
pid      = fpid.read()
lock  = threading.Lock()
state = State.MAP_BUILDING
send = ""

def action_on_transit(val, action):
	""" Do something upon transition to next state ONCE"""
	global send
	# print("Action : "),
	# print(action)
	
	if action is Action.APPEND:
		tts(AFFIRMS[action], (val,))
		send += str(val)
		print(send)
	elif action is Action.CLEAR:
		tts(AFFIRMS[action])
		print(send)
		clear_send()
	elif action is Action.DOWNLOAD_MAP:
		tts(AFFIRMS[action])
		print(send)
		os.write(pipe_out, "*" + "\n")
		os.kill(int(pid), signal.SIGUSR2)
	elif action is Action.CONFIRM_BUILDING:
		tts(AFFIRMS[action], (send,))
		print(send)
		os.write(pipe_out, send + "\n")
		os.kill(int(pid), signal.SIGUSR2)
		clear_send()
	elif action is Action.CONFIRM_LEVEL:
		tts(AFFIRMS[action], (send,))
		print(send)
		os.write(pipe_out, send + "\n")
		os.kill(int(pid), signal.SIGUSR2)
		clear_send()
	elif action is Action.CONFIRM_START:
		print(send)
		tts(AFFIRMS[action], (send,))
		os.write(pipe_out, send + "\n")
		os.kill(int(pid), signal.SIGUSR2)
		clear_send()
	elif action is Action.CONFIRM_END:
		tts(AFFIRMS[action], (send,))
		print(send)
		os.write(pipe_out, send + "\n")
		os.kill(int(pid), signal.SIGUSR2)
		clear_send()
	elif action is Action.INCR:
		print(send)
		os.write(pipe_out, "++\n")
		os.kill(int(pid), signal.SIGUSR2)
	elif action is Action.DECR:
		print(send)
		os.write(pipe_out, "--\n")
		os.kill(int(pid), signal.SIGUSR2)
	elif action is Action.PLAY_MUSIC:
		print(send)
		args = shlex.split("omxplayer --vol -2000 good_life_remix.mp3")
		process = subprocess.Popen(args)
	elif action is Action.QUIT:
		print(send)
		os.write(pipe_out, "q\n")
		os.kill(int(pid), signal.SIGUSR2)
	elif action is Action.NULL:
		pass
	elif action is Action.NAV:
		os.write(pipe_out, "NAVIGATE\n")
		os.kill(int(pid), signal.SIGUSR2)
		pass
	elif action is Action.START:
		tts(AFFIRMS[action])
		pass
	elif action is Action.GET_INSTR:
		os.write(pipe_out, "GET_INSTR\n")
		os.kill(int(pid), signal.SIGUSR2)
		pass
	elif action is Action.GET_PREV:
		os.write(pipe_out, "GET_PREV\n")
		os.kill(int(pid), signal.SIGUSR2)
		pass
	elif action is Action.REACHED:
		tts(AFFIRMS[action])
		os.write(pipe_out, "USER_CHECKPOINT_REACHED\n")
		os.kill(int(pid), signal.SIGUSR2)
		pass
	elif action is Action.STEP_OFF:
		tts(AFFIRMS[action])
		os.write(pipe_out, "STEP_OFF\n")
		os.kill(int(pid), signal.SIGUSR2)
		pass
	elif action is Action.STEP_ON:
		tts(AFFIRMS[action])
		os.write(pipe_out, "STEP_ON\n")
		os.kill(int(pid), signal.SIGUSR2)
		pass
	else:
		raise Exception("Unrecognized action!")

def clear_send():
	global send
	send = ''

def handler(key):
	# Construct key object
	print("Key triggered : %s" % str(key.value))
	global state
	for transition in key.types:
		try:
			# Ensure that only one interrupt is processed at a time
			lock.acquire()
			(state, action) = State.transitions[state][transition]
			action_on_transit(key.value, action)
		except KeyError as e:
			pass
		finally:
			lock.release()

def setup():
	for j in COL:
		GPIO.setup(j, GPIO.OUT)
		GPIO.output(j, 1)

	for i in ROW:
		GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def run():
	pass

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
	setup()
	tts("Software ready! Please enter building number")
	try:
		while(True):
			for j in COL:
				GPIO.output(j, 0)
				for i in ROW:
					if (GPIO.input(i) == 0):
						if not MATRIX[i][j]:
							MATRIX[i][j] = True
							time.sleep(0.1)
							key = KEY((i, j))
							handler(key)
							while(GPIO.input(i) == 0):
								pass
						else:
							# Key is already pressed
							pass
					else:
						MATRIX[i][j] = False
						pass
				GPIO.output(j, 1)
	except KeyboardInterrupt as e:
		GPIO.cleanup()
	except Exception as e:
		print e

if __name__ == "__main__":
	main()