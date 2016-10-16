from enum import Enum
import re

class Transitions(Enum):
	""" Actions can be emitted by user (KEY prefixed), or triggered by software (SW prefixed) """
	KEY_NODE         = 0
	KEY_RESET        = 1
	KEY_WHERE_AM_I   = 2
	KEY_RESTART      = 3
	SW_REACHED_NODE  = 4
	SW_READY         = 5
	KEY_SHUTDOWN     = 6

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
		elif string == 'CHECKPOINT_REACHED':
			return (Transitions.SW_REACHED_NODE, string)
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
		Transitions.KEY_RESET : State.RESET
	},
	State.ACCEPT_END : {
		Transitions.KEY_NODE : State.NAVIGATING,
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESET : State.RESET
	},
	State.NAVIGATING: {
		Transitions.SW_REACHED_NODE : State.REACHED,
		Transitions.KEY_RESTART : State.ACCEPT_START,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.REACHED: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESTART : State.ACCEPT_START,
		Transitions.KEY_RESET : State.RESET
	},
	State.RESET: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESTART: State.ACCEPT_START
	}
}