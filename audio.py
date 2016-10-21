import os, subprocess, shlex

def tts(instruction, placeholders=(), verbose=True):
	""" Queue instruction, do not execute yet"""
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	args = shlex.split('flite -t ' + "\"" + instruction % placeholders + "\"")
	subprocess.Popen(args)

if __name__ == "__main__":
	tts("hello world")
