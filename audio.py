import os, subprocess, shlex

def tts(instruction, placeholders=(), verbose=True):
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	args = shlex.split('flite -t ' + ("\"" + instruction % placeholders + "\""))
	process = subprocess.Popen(args)
