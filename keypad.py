from enum import Enum
from audio import AudioQueue
from Queue import Queue
import RPi.GPIO as GPIO
import time, os, signal, json, shlex, subprocess, threading
from threading import Thread

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
	KEY_MUSIC = 5

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
	PLAY_MUSIC    = 9

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
		Transitions.KEY_STAR : (State.FFA, Action.CONFIRM_END)
	},
	State.FFA : {
		Transitions.KEY_INCR : (State.FFA, Action.INCR),
		Transitions.KEY_DECR : (State.FFA, Action.DECR),
		Transitions.KEY_HASH : (State.START, Action.NULL),
		Transitions.KEY_STAR : (State.FFA, Action.QUIT),
		Transitions.KEY_MUSIC : (State.FFA, Action.PLAY_MUSIC)
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
lock  = threading.Lock()
state = State.START
send = ''
# MATRIX = [
# 	[1,2,3],    (25,22), (25,17), (25,4)
# 	[4,5,6],    (24,22), (24,17), (24,4)
# 	[7,8,9],    (23,22), (23,17), (23,4)
# 	["#",0,"*"] (18,22), (18,17), (18,4)
# 	]
ROW = [18,23,24,25] # G, H, J, K
COL = [4,17,22] # D, E, F
def action_on_transit(aq, val, action):
	""" Do something upon transition to next state ONCE"""
	global send
	print("Action : "),
	print(action)
	
	if action is Action.APPEND:
		aq.tts(AFFIRMS[action], (val,))
		send += str(val)
	elif action is Action.CLEAR:
		aq.tts(AFFIRMS[action])
		clear_send()
	elif action is Action.CONFIRM_START:
		aq.tts(AFFIRMS[action], (send,))
		clear_send()
		# os.write(pipe_out, send + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.CONFIRM_END:
		aq.tts(AFFIRMS[action], (send,))
		clear_send()
		# os.write(pipe_out, send + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.INCR:
		# os.write(pipe_out, "++\r\n" + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.DECR:
		# os.write(pipe_out, "--\r\n" + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.PLAY_MUSIC:
		args = shlex.split("omxplayer --vol -2000 good_life_remix.mp3")
		process = subprocess.Popen(args)
		print(send)
	elif action is Action.QUIT:
		# os.write(pipe_out, "q" + "\r\n")
		# os.kill(int(pid), signal.SIGUSR2)
		print(send)
	elif action is Action.NULL:
		pass
	else:
		raise Exception("Unrecognized action!")
	
	# Issue prompts for all the transitions in current state
	for transition in State.transitions[state]:
		aq.tts(PROMPTS[transition])

def clear_send():
	global send
	send = ''

def handler(aq, key):
	# Construct key object
	print("Key triggered : %s" % str(key.value))
	global state
	for transition in key.types:
		try:
			# Ensure that only one interrupt is processed at a time
			lock.acquire()
			(state, action) = State.transitions[state][transition]
			action_on_transit(aq, key.value, action)
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

def start_audio_queue(q):
	return AudioQueue(q)

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
	aq = start_audio_queue()
	for i in range(NUM_WORKERS):
		t = Thread(target=aq.run)
		t.daemon = True
		t.start()

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
							handler(aq, key)
						else:
							# Key is already pressed
							pass
					else:
						MATRIX[i][j] = False
						pass
				GPIO.output(j, 1)
	except KeyboardInterrupt as e:
		GPIO.cleanup()

if __name__ == "__main__":
	main()