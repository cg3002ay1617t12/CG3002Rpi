import path_finder
import random, math, os, signal
from fsm import *

# Global variables


def init():
	""" Start child processes, setup pipes, download and parse map"""
	pass

def main():
	""" Main program of the Finite State Machine"""
	def transition_handler(signum, frame):
		pass
	state = State.START
	init()
	while True:
		if state is State.END:
			break
		try:
			# Wait for state transitions to occur
			state = State.transitions[state][transition]
		except KeyError as e:
			pass
	# Clean up system resources, close files and pipes, delete temp files
	sys.exit(1)

if __name__ == "__main__":
	main()