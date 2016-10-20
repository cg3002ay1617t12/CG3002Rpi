from enum import Enum
import re

class Transitions(Enum):
	""" Actions can be emitted by user (KEY prefixed), or triggered by software (SW prefixed) """
	KEY_NODE         = 0
	KEY_RESET        = 1
	KEY_WHERE_AM_I   = 2
	KEY_RESTART      = 3
	KEY_INCR         = 4
	KEY_DECR         = 5
	SW_REACHED_NODE  = 6
	SW_READY         = 7
	KEY_SHUTDOWN     = 8
	KEY_NAV          = 9

	@classmethod
	def reverse_mapping(cls, value):
		for i,v in enumerate(Transitions):
			if value == i:
				return v
		return None

	@classmethod
	def recognize_input(cls, string):
		"""Define keystrokes for valid transitions here"""
		node   = re.compile(r"^(\d\d)$")
		string = string.strip('\r\n')
		match  = re.match(node, string)
		if match is not None:
			return (Transitions.KEY_NODE, match.group())
		elif string == 'r':
			return (Transitions.KEY_RESET, string)
		elif string == 'w':
			return (Transitions.KEY_WHERE_AM_I, string)
		elif string == 'q':
			return (Transitions.KEY_SHUTDOWN, string)
		elif string == '*':
			return (Transitions.KEY_RESTART, string)
		elif string == '++':
			return (Transitions.KEY_INCR, string)
		elif string == '--':
			return (Transitions.KEY_DECR, string)
		elif string == 'CHECKPOINT_REACHED':
			return (Transitions.SW_REACHED_NODE, string)
		elif string == 'NAVIGATE':
			return (Transitions.KEY_NAV, string)
		elif string == 'SW_READY':
			return (Transitions.SW_READY, string)
		else:
			return None

class State(Enum):
	START        = 0
	ACCEPT_START = 1
	ACCEPT_END   = 2
	NAVIGATING   = 3
	REACHED      = 4
	RESET        = 5
	END          = 6

	@classmethod
	def reverse_mapping(cls, value):
		for i,v in enumerate(Transitions):
			if value == i:
				return v
		return None

State.transitions = {
	State.START: {
		Transitions.SW_READY : State.ACCEPT_START
	},
	State.ACCEPT_START: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_NODE : State.ACCEPT_END,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_INCR : State.ACCEPT_START,
		Transitions.KEY_DECR : State.ACCEPT_START
	},
	State.ACCEPT_END : {
		Transitions.KEY_NODE : State.NAVIGATING,
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_INCR : State.ACCEPT_END,
		Transitions.KEY_DECR : State.ACCEPT_END
	},
	State.NAVIGATING: {
		Transitions.SW_REACHED_NODE : State.REACHED,
		Transitions.KEY_RESTART : State.ACCEPT_START,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_INCR : State.NAVIGATING,
		Transitions.KEY_DECR : State.NAVIGATING,
	},
	State.REACHED: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESTART : State.ACCEPT_START,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_INCR : State.REACHED,
		Transitions.KEY_DECR : State.REACHED,
		Transitions.KEY_NAV : State.NAVIGATING
	},
	State.RESET: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESTART: State.ACCEPT_START
	}
}