class Localization(object):

	def __init__(self, x=None, y=None, bearing=None):
		self.bearing = bearing if bearing is not None else 0
		self.x       = x if x is not None else 0
		self.y       = y if y is not None else 0

	def update():
		pass