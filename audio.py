import os, subprocess, shlex

def tts(instruction, placeholders=(), verbose=True):
	""" Queue instruction, do not execute yet"""
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	cmd = shlex.split('flite -t ' + "\"" + instruction % placeholders + "\"")
	subprocess.Popen(cmd)

if __name__ == "__main__":
	pass
	tts("hello world")
