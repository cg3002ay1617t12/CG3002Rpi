import os, subprocess, shlex
from collections import deque
from Queue import Queue

class AudioQueue(object):
	def __init__(self, q=None):
		if q is None:
			self.q = Queue(maxsize=10)
		else:
			self.q = q

	def tts(self, instruction, placeholders=(), verbose=True):
		""" Queue instruction, do not execute yet"""
		if verbose:
			print("[INSTRUCTION] : "),
			print(instruction % placeholders)
		args = shlex.split('flite -t ' + ("\"" + instruction % placeholders + "\""))
		self.q.put(args)
		print("tts : "),
		print(self.q.qsize())

	def run(self):
		""" Target function for threaded worker"""
		while True:
			print("run : "),
			print(self.q.qsize())
			process = subprocess.Popen(self.q.get())
			print("Process opened")
			process.wait()
			self.q.task_done()

if __name__ == "__main__":
	q = AudioQueue()
	q.run()