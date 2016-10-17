import os, subprocess, shlex
from collections import deque

class AudioQueue(object):
	def __init__(self):
		self.q = deque(maxlen=10)

	def tts(self, instruction, placeholders=(), verbose=True):
		""" Queue instruction, do not execute yet"""
		if verbose:
			print("[INSTRUCTION] : "),
			print(instruction % placeholders)
		args = shlex.split('flite -t ' + ("\"" + instruction % placeholders + "\""))
		self.q.append(args)
		print("tts : "),
		print(len(self.q))

	def run(self):
		while True:
			print("run : "),
			print(len(self.q))
			if len(self.q) > 0:
				process = subprocess.Popen(self.q.popleft())
				print("Process opened")
				process.wait()

if __name__ == "__main__":
	q = AudioQueue()
	q.run()