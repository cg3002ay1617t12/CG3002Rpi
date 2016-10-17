import os

def tts(instruction, placeholders=(), verbose=True):
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	print instruction
	os.system('flite -t ' + ("\"" + instruction + "\"" % placeholders))
