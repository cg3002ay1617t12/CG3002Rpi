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
	KEY_REACHED_NODE = 7
	SW_READY         = 8
	KEY_SHUTDOWN     = 9
	KEY_NAV          = 10
	KEY_DOWNLOAD     = 11
	KEY_GET_INSTR    = 12
	KEY_GET_PREV     = 13
	KEY_STEP_ON      = 14
	KEY_STEP_OFF     = 15

	@classmethod
	def reverse_mapping(cls, value):
		for i,v in enumerate(Transitions):
			if value == i:
				return v
		return None

	@classmethod
	def recognize_input(cls, string):
		"""Define keystrokes for valid transitions here"""
		node   = re.compile(r"^(\d+)$")
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
		elif string == 'DOWNLOAD_MAP':
			return (Transitions.KEY_DOWNLOAD, string)
		elif string == 'CHECKPOINT_REACHED':
			return (Transitions.SW_REACHED_NODE, string)
		elif string == 'USER_CHECKPOINT_REACHED':
			return (Transitions.KEY_REACHED_NODE, string)
		elif string == 'NAVIGATE':
			return (Transitions.KEY_NAV, string)
		elif string == 'SW_READY':
			return (Transitions.SW_READY, string)
		elif string == 'GET_INSTR':
			return (Transitions.KEY_GET_INSTR, string)
		elif string == 'GET_PREV':
			return (Transitions.KEY_GET_PREV, string)
		elif string == 'STEP_ON':
			return (Transitions.KEY_STEP_ON, string)
		elif string == 'STEP_OFF':
			return (Transitions.KEY_STEP_OFF, string)
		else:
			return None

class State(Enum):
	START                 = 0
	ACCEPT_START_BUILDING = 1
	ACCEPT_START_LEVEL    = 2
	ACCEPT_START          = 3
	ACCEPT_END_BUILDING   = 4
	ACCEPT_END_LEVEL      = 5
	ACCEPT_END            = 6
	NAVIGATING            = 7
	REACHED               = 8
	RESET                 = 9
	END                   = 10

	@classmethod
	def reverse_mapping(cls, value):
		for i,v in enumerate(Transitions):
			if value == i:
				return v
		return None

State.transitions = {
	State.START: {
		Transitions.SW_READY : State.ACCEPT_START_BUILDING
	},
	State.ACCEPT_START_BUILDING : {
		Transitions.KEY_NODE : State.ACCEPT_START_LEVEL,
		Transitions.KEY_DECR : State.ACCEPT_START_BUILDING,
		Transitions.KEY_INCR : State.ACCEPT_START_BUILDING,
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.ACCEPT_START_LEVEL : {
		Transitions.KEY_INCR : State.ACCEPT_START_LEVEL,
		Transitions.KEY_DECR : State.ACCEPT_START_LEVEL,
		Transitions.KEY_NODE : State.ACCEPT_START,
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.ACCEPT_START: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_NODE : State.ACCEPT_END_BUILDING,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_INCR : State.ACCEPT_START,
		Transitions.KEY_DECR : State.ACCEPT_START
	},
	State.ACCEPT_END_BUILDING : {
		Transitions.KEY_NODE : State.ACCEPT_END_LEVEL,
		Transitions.KEY_DECR : State.ACCEPT_END_BUILDING,
		Transitions.KEY_INCR : State.ACCEPT_END_BUILDING,
		Transitions.KEY_SHUTDOWN : State.END
	},
	State.ACCEPT_END_LEVEL : {
		Transitions.KEY_INCR : State.ACCEPT_END_LEVEL,
		Transitions.KEY_DECR : State.ACCEPT_END_LEVEL,
		Transitions.KEY_NODE : State.ACCEPT_END,
		Transitions.KEY_SHUTDOWN : State.END
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
		Transitions.KEY_REACHED_NODE : State.REACHED,
		Transitions.KEY_RESTART : State.ACCEPT_START_BUILDING,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_INCR : State.NAVIGATING,
		Transitions.KEY_DECR : State.NAVIGATING,
		Transitions.KEY_GET_INSTR : State.NAVIGATING,
		Transitions.KEY_GET_PREV : State.NAVIGATING,
		Transitions.KEY_STEP_ON : State.NAVIGATING,
		Transitions.KEY_STEP_OFF : State.NAVIGATING
	},
	State.REACHED: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESTART : State.ACCEPT_START_BUILDING,
		Transitions.KEY_RESET : State.RESET,
		Transitions.KEY_INCR : State.REACHED,
		Transitions.KEY_DECR : State.REACHED,
		Transitions.KEY_NAV : State.NAVIGATING,
		Transitions.KEY_GET_INSTR : State.REACHED,
		Transitions.KEY_GET_PREV : State.REACHED,
		Transitions.KEY_STEP_ON : State.REACHED,
		Transitions.KEY_STEP_OFF : State.REACHED
	},
	State.RESET: {
		Transitions.KEY_SHUTDOWN : State.END,
		Transitions.KEY_RESTART: State.ACCEPT_START_BUILDING
	}
}