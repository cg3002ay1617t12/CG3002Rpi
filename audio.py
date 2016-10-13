import os

def tts(instruction, placeholders=()):
	os.system(instruction % placeholders)
