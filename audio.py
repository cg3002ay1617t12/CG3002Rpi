import os, subprocess, shlex

def tts(instruction, placeholders=(), verbose=True):
	""" Execute command, blocking"""
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	cmd = shlex.split('flite -t ' + "\"" + instruction % placeholders + "\"")
	subprocess.Popen(cmd)

if __name__ == "__main__":
	tts("hello world")