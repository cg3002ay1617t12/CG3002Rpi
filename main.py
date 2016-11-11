from path_finder import PathFinder
from step_detection import StepDetector
import os, signal, sys, subprocess, shlex, time, json, threading, platform
from fsm import *
from localization import *
from audio import tts
from threading import Thread

class App(object):
	EVENT_PIPE = './event_pipe'
	DATA_PIPE  = './data_pipe'
	INSTRUCTION_INTERVAL = 8
	
	def __init__(self):
		self.platform_ = platform.platform()
		self.pid = os.getpid()
		fpid = open('./pid', 'w')
		fpid.write(str(self.pid))
		fpid.close()
		
		self.is_stepcounter_on = False
		self.curr_start_node = -1
		self.curr_end_node   = -1
		self.transit         = False
		self.userinput       = ''
		self.transition      = None
		self.instruction     = ""
		self.start           = time.time()
		self.platform_pi = ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", 
							"Linux-4.4.13+-armv6l-with-debian-8.0", 
							"Linux-4.4.30+-armv6l-with-debian-8.0"]
		# Init submodules
		if self.platform_ in self.platform_pi:
			plot = False
		else:
			plot = False
		self.PathFinder   = PathFinder()
		self.StepDetector = StepDetector(plot=plot)
		self.Localization = Localization(x=0, y=0, north=self.PathFinder.get_angle_of_north(), plot=plot)
		# self.LPF = LocalPathFinder(mode='demo')

		# Init environment and user-defined variables
		try:
			self.ENV                           = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
			StepDetector.SAMPLES_PER_PACKET    = self.ENV["STEP_SAMPLES_PER_PACKET"]
			StepDetector.SAMPLES_PER_WINDOW    = self.ENV["STEP_SAMPLES_PER_WINDOW"]
			StepDetector.INTERRUPTS_PER_WINDOW = StepDetector.SAMPLES_PER_WINDOW / StepDetector.SAMPLES_PER_PACKET
			self.StepDetector.THRES            = self.ENV["STEP_THRES"]
			self.Localization.stride           = self.ENV["STRIDE_LENGTH"]
			App.DATA_PIPE                      = self.ENV['DATA_PIPE']
			App.EVENT_PIPE                     = self.ENV['EVENT_PIPE']
		except Exception as e:
			print("[MAIN] Environment file not found, using defaults instead")
		
	def setup_pipes(self):
		# Setting up IPC
		self.master = True
		self.state = State.START
		pipe_desc = os.open(App.DATA_PIPE, os.O_RDONLY)
		print("[MAIN] Starting data pipe...listening for serial comms...")
		self.data_pipe = os.fdopen(pipe_desc)
		print("[MAIN] Serial comms connected!")
		pipe_desc = os.open(App.EVENT_PIPE, os.O_RDWR)
		print("[MAIN] Starting event pipe...listening for keystrokes...")
		self.event_pipe = os.fdopen(pipe_desc, 'w+')
		print("[MAIN] Keypad connected!")
		fpid = open('./serial_pid', 'r')
		app.serial_pid = fpid.read()
		fpid.close()
		fpid = open('./keypad_pid', 'r')
		app.keypad_pid = fpid.read()
		fpid.close()

	def register_handler(self):
		signal.signal(signal.SIGUSR2, transition_handler)
		signal.signal(signal.SIGUSR1, serial_handler)

	def issue_instruction(self):
		""" Only issue instruction after interval"""
		tts(self.instruction)
		self.instruction = ""

	def build_instruction(self, instr, placeholders=()):
		self.instruction += instr % placeholders

	def clear_instruction(self):
		self.instruction = ""

	def update_steps(self, angle=None):
		if self.transition is Transitions.KEY_INCR:
			self.StepDetector.incr_step()
			self.Localization.incr_step(direction=angle)
		elif self.transition is Transitions.KEY_DECR:
			self.StepDetector.decr_step()
			self.Localization.decr_step(direction=angle)
		else:
			pass

	def get_instruction(self):
		angle = self.PathFinder.get_angle_to_next_node()
		if self.transition in [Transitions.KEY_GET_INSTR, Transitions.KEY_DECR, Transitions.KEY_INCR]:
			reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
			if reached:
				self.curr_reached_node_instr = self.PathFinder.get_audio_reached(reached_node)
				self.build_instruction(self.curr_reached_node_instr)
			else:
				self.build_instruction(self.PathFinder.get_audio_next_instruction())
		else:
			pass
		self.issue_instruction()
		self.clear_instruction()

	def combine_node_from_building_and_level(self):
		""" Only call this once user has keyed in start and end node """
		self.start_prefix = -100
		self.end_prefix = -100
		if self.start_building == 1 and self.start_level == 1:
			self.start_prefix = 0
		elif self.start_building == 1 and self.start_level == 2:
			self.start_prefix = 100
		elif self.start_building == 2 and self.start_level == 2:
			self.start_prefix = 200
		elif self.start_building == 2 and self.start_level == 3:
			self.start_prefix = 300
		else:
			print("[MAIN] Error invalid start building and level given!")

		if self.end_building == 1 and self.end_level == 1:
			self.end_prefix = 0
		elif self.end_building == 1 and self.end_level == 2:
			self.end_prefix = 100
		elif self.end_building == 2 and self.end_level == 2:
			self.end_prefix = 200
		elif self.end_building == 2 and self.end_level == 3:
			self.end_prefix = 300
		else:
			print("[MAIN] Error invalid end building and level given!")
		return (int(self.start_prefix + self.curr_start_node), int(self.end_prefix + self.curr_end_node)) # Start node , end node


	def run_once_on_transition(self, userinput):
		""" Run once upon transition to new state"""
		print("[MAIN] TRANSITION : " + str(self.state))
		if self.state is State.END:
			tts("Shutting down.")
			pass
		elif self.state is State.ACCEPT_START_BUILDING:
			# tts("Please enter building")
			if self.transition is Transitions.KEY_NODE:
				try:
					self.start_building = int(userinput)
				except Exception as e:
					print e
			pass
		elif self.state is State.ACCEPT_START_LEVEL:
			# tts("Please enter level")
			if self.transition is Transitions.KEY_NODE:
				try:
					self.start_level = int(userinput)
					self.PathFinder = PathFinder()
				except ValueError as e:
					print("[MAIN] Error! Wrong building and level entered")
					tts("Please enter a valid building and level")
				except Exception as e:
					print(e)
			pass
		elif self.state is State.ACCEPT_START:
			# tts("Please enter start node")
			if self.transition is Transitions.KEY_NODE:
				try:
					self.curr_start_node = int(userinput)
				except Exception as e:
					print '[MAIN] AEND exception'
					print e
			pass
		elif self.state is State.ACCEPT_END_BUILDING:
			# tts("Please enter building")
			if self.transition is Transitions.KEY_NODE:
				try:
					self.end_building = int(userinput)
				except Exception as e:
					print e
			pass
		elif self.state is State.ACCEPT_END_LEVEL:
			# tts("Please enter level")
			if self.transition is Transitions.KEY_NODE:
				try:
					self.end_level = int(userinput)
					self.PathFinder = PathFinder()
				except ValueError as e:
					print("[MAIN] Error! Wrong building and level entered")
					tts("Please enter a valid building and level")
				except Exception as e:
					print(e)
			pass
		elif self.state is State.ACCEPT_END:
			# tts("Please enter end destination")
			if self.transition is Transitions.KEY_NODE:
				try:
					self.curr_end_node = int(userinput)
					(self.combined_start_node, self.combined_end_node) = self.combine_node_from_building_and_level()
					(x, y)  = self.PathFinder.get_coordinates_from_node(self.combined_start_node)
					if x is None and y is None:
						print("[MAIN] Error! Invalid start node given, please try again")
						tts("Error, invalid start, please enter again")
					else:
						bearing = self.Localization.stabilized_bearing
						self.PathFinder.update_coordinate(x, y, bearing)
						self.Localization.update_coordinates(x, y)
						self.update_steps()
					self.PathFinder.update_source_and_target(self.combined_start_node, self.combined_end_node)
					print("[MAIN] Source : %d, Dest: %d" % (self.combined_start_node, self.combined_end_node))
					print("[MAIN] Current location: %.2f, %.2f, %.2f" % (self.PathFinder.get_x_coordinate(), self.PathFinder.get_y_coordinate(), self.Localization.stabilized_bearing))
				except Exception as e:
					print e
					pass
			pass
		elif self.state is State.NAVIGATING:
			print("[MAIN] Transition for State.NAVIGATING")
			bearing = self.Localization.stabilized_bearing
			(x, y)  = self.PathFinder.get_coordinates_from_node(self.curr_start_node)
			if self.transition is Transitions.KEY_GET_PREV:
				tts("Previous " + str(self.PathFinder.get_prev_visited_node()))
			elif self.transition is Transitions.SW_REACHED_NODE:
				print("[MAIN] %s triggered " % (str(self.transition)))
			elif self.transition is Transitions.KEY_REACHED_NODE:
				# When user press 6
				new_coord = self.PathFinder.get_next_coordinates()
				if new_coord[0] is not None and new_coord[1] is not None:
					self.Localization.update_coordinates(new_coord[0], new_coord[1])
					self.PathFinder.update_coordinate(new_coord[0], new_coord[1], self.Localization.stabilized_bearing)
				else:
					print("[MAIN] Error! Invalid new coordinates for reached node")
			elif self.transition is Transitions.KEY_GET_INSTR:
				self.get_instruction()
			elif self.transition is Transitions.KEY_DECR or self.transition is Transitions.KEY_INCR:
				angle = self.PathFinder.get_angle_to_next_node()
				self.update_steps(angle)
			elif self.transition is Transitions.KEY_RESTART:
				print("Restarting. Press start building and level")
				pass
			elif self.transition is Transitions.KEY_STEP_ON:
				self.is_stepcounter_on = True
			elif self.transition is Transitions.KEY_STEP_OFF:
				self.is_stepcounter_on = False
			else:
				print("[MAIN] Error unrecognized transition: %s" % str(self.transition))
				pass
		elif self.state is State.REACHED:
			print("[MAIN] Transition for State.REACHED")
			# self.curr_reached_node_instr = self.PathFinder.get_audio_reached(self.curr_end_node)
			if self.transition is Transitions.KEY_GET_PREV:
				tts("Previous " + str(self.PathFinder.get_prev_visited_node()))
			elif self.transition is Transitions.KEY_GET_INSTR:
				self.get_instruction()
			elif self.transition is Transitions.KEY_DECR or self.transition is Transitions.KEY_INCR:
				angle = self.PathFinder.get_angle_to_next_node()
				self.update_steps(angle)
			elif self.transition is Transitions.KEY_NAV:
				print("[MAIN] %s triggered " % (str(self.transition)))
			elif self.transition is Transitions.KEY_RESTART:
				print("[MAIN] unhandled Transition : %s" % str(self.transition))
				pass
			elif self.transition is Transitions.KEY_SHUTDOWN:
				print("[MAIN] %s triggered " % str(self.transition))
				pass
			elif self.transition is Transitions.KEY_RESTART:
				tts("Restarting. Press building and level")
			elif self.transition is Transitions.KEY_STEP_ON:
				self.is_stepcounter_on = True
			elif self.transition is Transitions.KEY_STEP_OFF:
				self.is_stepcounter_on = False
			else:
				print("[MAIN] Error unrecognized transition: %s" % str(self.transition))
				pass
		elif self.state is State.RESET:
			tts("Resetting. ")
			self.StepDetector.reset_step()
			self.Localization.reset()
			pass
		else:
			pass
		try:
			self.state   = State.transitions[self.state][self.transition]
		except KeyError as e:
			print("[MAIN] Ignoring state %s -> transition %s " % (str(self.state), str(self.transition)))
			print e

		print("[MAIN] " + str(self.state))
		self.transit = False

	def run(self):
		""" Run forever and multiplex between the states """
		while True:
			if self.transit:
				self.run_once_on_transition(self.userinput)
			try:
				if self.state is State.END:
					break
				elif self.state is State.ACCEPT_START_BUILDING:
					# self.Localization.run(self.StepDetector.curr_steps)
					pass
				elif self.state is State.ACCEPT_START_LEVEL:
					# self.Localization.run(self.StepDetector.curr_steps)
					pass
				elif self.state is State.ACCEPT_START:
					# Do something, make sure its non-blocking
					# self.Localization.run(self.StepDetector.curr_steps)
					# Cannot do anything because we do not know where the user is
					pass
				elif self.state is State.ACCEPT_END_BUILDING:
					pass
				elif self.state is State.ACCEPT_END_LEVEL:
					pass
				elif self.state is State.ACCEPT_END:
					# Do something, make sure its non-blocking
					# self.Localization.run(self.StepDetector.curr_steps)
					# Wait for user to key in destination
					pass
				elif self.state is State.NAVIGATING:
					# Do something, make sure its non-blocking
					if self.is_stepcounter_on: self.StepDetector.run()
					angle = self.PathFinder.get_angle_to_next_node()
					self.Localization.run(self.StepDetector.curr_steps, angle=angle)
					if self.StepDetector.curr_steps > 0:
						self.build_instruction("Step. ")
					if time.time() - self.start > 5:
						print("[MAIN] Heading : %.2f" % (self.Localization.stabilized_bearing))
						self.start = time.time()
					reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
					if reached:
						self.curr_reached_node_instr = self.PathFinder.get_audio_reached(reached_node)
						self.build_instruction(self.curr_reached_node_instr)
						(x, y) = self.PathFinder.get_coordinates_from_node(reached_node)
						self.Localization.update_coordinates(x, y)
						self.issue_instruction()
						self.StepDetector.curr_steps = 0
						# Transit to REACHED state
						self.event_pipe.write("CHECKPOINT_REACHED\r\n")
						os.kill(self.pid, signal.SIGUSR2)
					else:
						self.build_instruction(self.PathFinder.get_audio_next_instruction())
					if self.StepDetector.curr_steps > 0:
						self.issue_instruction()
					self.StepDetector.curr_steps = 0
					self.clear_instruction()
					pass
				elif self.state is State.REACHED:
					# Do something, make sure its non-blocking
					if self.is_stepcounter_on: self.StepDetector.run()
					angle = self.PathFinder.get_angle_to_next_node()
					self.Localization.run(self.StepDetector.curr_steps, angle=angle)
					if self.StepDetector.curr_steps > 0:
						self.build_instruction("Step. ")
					if time.time() - self.start > 5:
						self.start = time.time()
						print("[MAIN] Heading is : %.2f " % (self.Localization.stabilized_bearing))	
					reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
					if reached:
						self.curr_reached_node_instr = self.PathFinder.get_audio_reached(reached_node)
						self.build_instruction(self.PathFinder.get_audio_reached(reached_node))
					else:
						self.build_instruction("Arrived. ")
						self.build_instruction(self.curr_reached_node_instr)
						self.build_instruction(self.PathFinder.get_audio_next_instruction())
					if (self.StepDetector.curr_steps > 0):
						self.issue_instruction()
					self.StepDetector.curr_steps = 0
					self.clear_instruction()
					pass
				elif self.state is State.RESET:
					# Do something, make sure its non-blocking
					if self.is_stepcounter_on: self.StepDetector.run()
					angle = self.PathFinder.get_angle_to_next_node()
					self.Localization.run(self.StepDetector.curr_steps, angle=angle)
					if (self.StepDetector.curr_steps > 0):
						self.build_instruction("Step. ")	
					reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
					if reached:
						self.curr_reached_node_instr = self.PathFinder.get_audio_reached(reached_node)
						self.build_instruction(self.PathFinder.get_audio_reached(reached_node))
					else:
						self.build_instruction(self.PathFinder.get_audio_next_instruction())
					if self.StepDetector.curr_steps > 0:
						self.issue_instruction()
					self.StepDetector.curr_steps = 0
					self.clear_instruction()
					pass
				else:
					pass
			except Exception as e:
				print(e)
		# Clean up system resources, close files and pipes, delete temp files
		os.kill(int(self.serial_pid), signal.SIGTERM)
		os.kill(int(self.keypad_pid), signal.SIGTERM)
		sys.exit(0)

app = App()
def timeout_handler():
	global app
	try:
		os.kill(int(app.serial_pid), signal.SIGUSR1)
		print("[MAIN] Killed serial process %s" % app.serial_pid)
		tts("Error...timeout on serial data. Check Arduino connection and reset when ready")
	except Exception as e:
		pass # Process may have terminated already
	connect_picomms(platform=app.platform_)

def transition_handler(signum, frame, *args, **kwargs):
	""" Asynchronous event handler to trigger state transitions"""
	global app
	event = app.event_pipe.readline()
	(transition, userinput) = Transitions.recognize_input(event)
	print("[MAIN] " + str(transition))
	try:
		app.transit    = True
		app.userinput  = userinput
		app.transition = transition
	except KeyError as e:
		print e
		pass

def serial_handler(signum, frame, *args, **kwargs):
	""" Handles all incoming sensor data and distribute to the relevant submodules"""
	global app
	def process_rpi(datum):
		""" Run this if using the pi_comms protocol"""
		(component_id, readings) = datum.split('~')
		component_id = int(component_id)
		try:
			if component_id == 1:
				(a_x, a_y, a_z) = map(lambda x: x.strip('\0\r\n\t'), readings.split(','))
				app.StepDetector.ax.append(float(a_x))
				app.StepDetector.ay.append(float(a_y))
				app.StepDetector.az.append(float(a_z))
			if component_id == 2:
				heading = readings.strip('\r\n').strip('\0\n\r\t')
				app.Localization.heading.append(float(heading))
			if component_id == 3:
				(g_x, g_y, g_z) = map(lambda x: x.strip(' \0\r\n\t'), readings.split(','))
				app.Localization.rotate_x.append(float(g_x))
				app.Localization.rotate_y.append(float(g_y))
				app.Localization.rotate_z.append(float(g_z))
		except ValueError as e:
			print e
	
	def process_laptop(datum):
		""" Run this if not using the pi_comms protocol"""
		try:
			(x,y,z,a,b,c,d) = map(lambda x: x.strip('\r\n'), datum.split(','))
			app.StepDetector.ax.append(float(x))
			app.StepDetector.ay.append(float(y))
			app.StepDetector.az.append(float(z))
			app.Localization.heading.append(float(d))
			app.Localization.rotate_x.append(float(a))
			app.Localization.rotate_y.append(float(b))
			app.Localization.rotate_z.append(float(c))
		except ValueError as e:
			print e
	# terminate process in timeout seconds
	timeout    = 2 # seconds
	timer      = threading.Timer(timeout, timeout_handler)
	timer.start()
	line_count = StepDetector.SAMPLES_PER_PACKET
	buffer_    = []
	while line_count > 0:
		data = app.data_pipe.readline()
		buffer_.append(data)
		line_count -= 1
	timer.cancel()
	if app.platform_ in app.platform_pi:
		map(process_laptop, buffer_)
	else:
		map(process_laptop, buffer_)
		# map(process_laptop, buffer_)
	if time.time() - app.start > 5:
		print("[MAIN] Incoming serial data from Arduino")
		app.start = time.time()
	app.StepDetector.new_data = True
	app.Localization.new_data = True

def connect_keypad(app, platform=None):
	if platform in app.platform_pi:
		print("[MAIN] Connecting with Keypad...")
		cmd     = "python keypad.py"
	elif platform in ["Darwin-15.2.0-x86_64-i386-64bit", "Linux-3.4.0+-x86_64-with-Ubuntu-14.04-trusty"]:
		print("[MAIN] Connecting with Keyboard...")
		cmd     = "python keyboard_sim.py" # Mac, Windows, Ubuntu with connected keyboard
	else:
		print("[MAIN] Connecting with Keyboard...")
		cmd     = "python keyboard_sim.py" # Mac, Windows, Ubuntu with connected keyboard
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("[MAIN] Connection established!")
	return process

def connect_picomms(app, platform=None):
	print("[MAIN] Connecting with Arduino...")
	if platform in app.platform_pi:
		# cmd     = "python pi_comms.py"
		cmd     = "python serial_input.py"
	elif platform == "Darwin-15.2.0-x86_64-i386-64bit" or platform == "Linux-3.4.0+-x86_64-with-Ubuntu-14.04-trusty":
		# cmd     = "python serial_input.py"
		cmd     = "python pi_comms.py"
	else:
		cmd     = "python serial_input.py"
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("[MAIN] Connection established!")
	return process

def main():
	""" Main program of the Finite State Machine"""
	global app
	platform_ = platform.platform()
	if os.fork() == 0:
		# Child processes
		signal.signal(signal.SIGALRM, timeout_handler)
		p1 = connect_picomms(app, platform_)
		p2 = connect_keypad(app, platform_)
		fpid = open('./keypad_pid', 'w')
		fpid.write(str(p2.pid))
		fpid.close()
		os._exit(0)
	else:
		# Parent process
		app.register_handler()
		app.setup_pipes()
		# Transit to READY state
		app.event_pipe.write("SW_READY\r\n")
		os.kill(app.pid, signal.SIGUSR2)
		app.run()

if __name__ == "__main__":
	main()
