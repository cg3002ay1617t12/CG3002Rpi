from enum import Enum

class Transitions(Enum):
	""" Actions can be emitted by user (KEY prefixed), or triggered by software (SW prefixed) """
	KEY_ACCEPT_COORD = 0
	KEY_RESET        = 1
	KEY_WHERE_AM_I   = 2
	SW_REACHED_NODE  = 3
	SW_READY         = 4
	KEY_SHUTDOWN     = 5

	@classmethod
	def reverse_mapping(cls, value):
		for i,v in enumerate(Transitions):
			if value == i:
				return v
		return None

	@classmethod
	def recognize_input(cls, string):
		"""Define keystrokes for valid transitions here"""
		string = string.strip('\r\n')
		if string == 'a':
			return Transitions.KEY_ACCEPT_COORD
		elif string == 'r':
			return Transitions.KEY_RESET
		elif string == 'w':
			return Transitions.KEY_WHERE_AM_I
		elif string == 'q':
			return Transitions.KEY_SHUTDOWN
		elif string == 'CHECKPOINT_REACHED':
			return Transitions.SW_REACHED_NODE
		elif string == 'SW_READY':
			return Transitions.SW_READY
		else:
			return None

class State(Enum):
	START      = 0
	READY      = 1
	NAVIGATING = 2
	REACHED    = 3
	RESET      = 4
	END        = 5

	@classmethod
	def reverse_mapping(cls, value):
		for i,v in enumerate(Transitions):
			if value == i:
				return v
		return None
	
State.transitions = {
	State.START: {
		Transitions.SW_READY : State.READY
	},
	State.READY: {
		Transitions.KEY_ACCEPT_COORD : State.NAVIGATING,
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.NAVIGATING: {
		Transitions.KEY_ACCEPT_COORD : State.READY,
		Transitions.KEY_RESET : State.RESET,
		Transitions.SW_REACHED_NODE : State.REACHED,
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.REACHED: {
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.RESET: {
		Transitions.KEY_SHUTDOWN : State.END
	}
}