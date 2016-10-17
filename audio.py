import os, subprocess, shlex
from collections import deque

INSTR_QUEUE = deque(maxlen=10)
def tts(instruction, placeholders=(), verbose=True):
	""" Queue instruction, do not execute yet"""
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	args = shlex.split('flite -t ' + ("\"" + instruction % placeholders + "\""))
	INSTR_QUEUE.append(args)

def run():
	while True:
		if len(INSTR_QUEUE) > 0:
			process = subprocess.Popen(INSTR_QUEUE.popleft())
			process.wait()

if __name__ == "__main__":
	run()