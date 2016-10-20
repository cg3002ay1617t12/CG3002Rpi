import os


def tts(self, instruction, placeholders=(), verbose=True):
	""" Execute command, blocking"""
	if verbose:
		print("[INSTRUCTION] : "),
		print(instruction % placeholders)
	cmd = 'flite -t ' + ("\"" + instruction % placeholders + "\"")
	os.system(cmd)

if __name__ == "__main__":
	tts("hello world")