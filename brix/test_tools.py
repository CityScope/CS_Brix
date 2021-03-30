import random
import threading
from time import sleep
from .classes import Handler

def shuffle_geogrid_data(geogrid_data):
	'''
	Update function for geogrid_data that shuffles the ids of the cells. 
	Useful for testing.
	'''
	ids = [cell['id'] for cell in geogrid_data]
	random.shuffle(ids)
	for i,cell in zip(ids,geogrid_data):
		cell['id'] = i
	return geogrid_data

def flip_random(geogrid_data,types_set=[]):
	'''
	Update function for geogrid_data that randomly flips the type of one of the cells.
	'''
	flip_cell = random.choice(geogrid_data)
	new_type = random.choice([t for t in types_set if t!=flip_cell['name']])
	for cell in geogrid_data:
		if cell['id']==flip_cell['id']:
			cell['name'] = new_type
			break
	return geogrid_data
	

class User(Handler):
	'''
	Class that simulates a user doing changes to the grid.

	To use, instantiate the class, and run User.start_user().
	This will create a new thread with a user running. 
	'''
	def __init__(self,*args,sleep_time=7,**kwargs):
		super(User, self).__init__(*args,**kwargs)
		self.sleep_time = sleep_time
		self.types_set = list(self.get_GEOGRID()['properties']['types'].keys())
		self.name = 'Simulated user'
		self.run_user = True
		self.update_count = 0

	def run(self):
		'''
		Run method to be called by :func:`threading.Thread.start`. 
		'''
		self.user_sim()

	def listen(self,new_thread=False,showFront=True,append=False):
		raise NameError("Subclass `User` has no method `listen`.")

	def add_indicator(self,I,test=True):
		raise NameError("Subclass `User` has no method `add_indicator`.")

	def update_package(self,geogrid_data=None,append=False):
		raise NameError("Subclass `User` has no method `update_package`.")

	def user_sim(self):
		'''
		Simulates a user that changes the grid every sleep_time seconds.
		The user flips a random cell 90% of the time, and shuffles the whole grid the other 10% of the time. 
		There is a small chance that the user will reset the grid to its original setting. 
		'''
		self.run_user = True
		self.update_count = 0
		while self.run_user:
			sleep(self.sleep_time)
			r = random.random()
			if r>0.99:
				self.reset_geogrid_data()
			elif r>0.9:
				self.update_geogrid_data(shuffle_geogrid_data)
			else:
				self.update_geogrid_data(flip_random,types_set=self.types_set)
			self.update_count+=1

	def start_user(self):
		self.start()

	def stop_user(self):
		self.run_user = False

	def user_status(self):
		running_users = [thread.name for thread in threading.enumerate() if thread.name==self.name]
		if len(running_users)>0:
			print('1 Running user')
			print('Total updates:',self.update_count)
			print('To stop, run: U.stop_user()')
		else:
			print('No running users')
			print('To start, run: U.start_user()')


