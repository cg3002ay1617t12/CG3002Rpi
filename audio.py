import os, subprocess, shlex
from Queue import Queue

class AudioQueue(object):
	def __init__(self, q=None):
		if q is None:
			self.q = Queue(maxsize=100)
		else:
			self.q = q

	def tts(self, instruction, placeholders=(), verbose=True):
		""" Queue instruction, do not execute yet"""
		if verbose:
			print("[INSTRUCTION] : "),
			print(instruction % placeholders)
		cmd = shlex.split('flite -t ' + "\"" + instruction % placeholders + "\"")
		self.q.put(cmd)

	def run(self):
		""" Target function for threaded worker"""
		while True:
			process = subprocess.Popen(self.q.get())
			process.wait()
			self.q.task_done()


if __name__ == "__main__":
	pass
	# tts("hello world")
