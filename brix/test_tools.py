import random
import threading
import weakref
import numpy as np
import networkx as nx
import pandas as pd
import geopandas as gpd
import time
from shapely.geometry import shape
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

def flip_random(geogrid_data,types_set=[],fraction=None):
	'''
	Update function for geogrid_data that randomly flips the type of one of the cells.
	'''
	if fraction is not None:
		n_flips = int(fraction*len(geogrid_data))
	else:
		n_flips = 1

	if n_flips==1:
		flip_cell = random.choice(geogrid_data)
		flip_cell_ids = [flip_cell['id']]
		new_type = random.choice([t for t in types_set if t!=flip_cell['name']])
	else:
		flip_cell_ids = [cell['id'] for cell in random.sample(geogrid_data,n_flips)]
		new_type = random.choice([t for t in types_set])
	for cell in geogrid_data:
		if cell['id'] in flip_cell_ids:
			cell['name'] = new_type
	return geogrid_data

def make_cluster(geogrid_data,fraction=0.1):
	'''
	Update function for geogrid_data that propagates the type of a random cell to the neighboring cells.
	'''
	G = geogrid_data.as_graph()
	n_flips = int(fraction*len(geogrid_data))
	seed_cell = random.choice(geogrid_data)
	new_type = seed_cell['name']

	cutoff = int(0.5*(1+np.sqrt(1+4*n_flips)))
	neighs = nx.single_source_shortest_path_length(G, seed_cell['id'], cutoff=cutoff)
	neighs_k = {}
	for i,k in neighs.items():
		if k not in neighs_k.keys():
			neighs_k[k] = [i]
		else:
			neighs_k[k].append(i)
	flip_cell_ids = set()
	for k in range(cutoff+1):
		if len(flip_cell_ids)+len(neighs_k[k]) < n_flips:
			flip_cell_ids = flip_cell_ids|set(neighs_k[k])
		else:
			flip_cell_ids = flip_cell_ids|set(neighs_k[k][:n_flips-len(flip_cell_ids)])

	for cell in geogrid_data:
		if cell['id'] in flip_cell_ids:
			cell['name'] = new_type
	return geogrid_data


class User(Handler):
	'''
	Class that simulates a user doing changes to the grid.

	To use, instantiate the class, and run User.start_user().
	This will create a new thread with a user running. 
	'''
	_instances = set()
	def __init__(self,*args,sleep_time=7,name=None,**kwargs):
		super(User, self).__init__(*args,**kwargs)
		self.sleep_time = sleep_time
		self.types_set = list(self.get_GEOGRID()['properties']['types'].keys())
		self.name = ('Simulated user' if name is None else name)
		self.run_user = True
		self.update_count = 0
		self._instances.add(weakref.ref(self))

	@classmethod
	def getinstances(cls):
		dead = set()
		for ref in cls._instances:
			obj = ref()
			if obj is not None:
				yield obj
			else:
				dead.add(ref)
		cls._instances -= dead

	def run(self):
		'''
		Run method to be called by :func:`threading.Thread.start`. 
		'''
		self.user_sim(quietly=True)

	def listen(self,new_thread=False,showFront=True,append=False):
		raise NameError("Subclass `User` has no method `listen`.")

	def add_indicator(self,I,test=True):
		raise NameError("Subclass `User` has no method `add_indicator`.")

	def update_package(self,geogrid_data=None,append=False):
		raise NameError("Subclass `User` has no method `update_package`.")

	def user_sim(self,quietly=True):
		'''
		Simulates a user that changes the grid every sleep_time seconds.
		The user flips a random cell 90% of the time, and shuffles the whole grid the other 10% of the time. 
		There is a small chance that the user will reset the grid to its original setting. 
		'''
		self.run_user = True
		self.update_count = 0
		self.fail_count = 0
		while self.run_user:
			sleep(max([np.random.normal(self.sleep_time),0.5]))
			r = random.random()
			try:
				if r>0.9999:
					if not quietly:
						print('reset_geogrid_data')
					self.reset_geogrid_data()
				elif r>0.85:
					fraction = random.random()/4
					if not quietly:
						print('make_cluster:',fraction)
					self.update_geogrid_data(make_cluster,fraction=fraction)
				elif r>0.8:
					fraction = random.random()/16
					if not quietly:
						print('flip_random:',fraction)
					self.update_geogrid_data(flip_random,types_set=self.types_set,fraction=fraction)
				else:
					if not quietly:
						print('flip_random (one)')
					self.update_geogrid_data(flip_random,types_set=self.types_set)
				self.update_count+=1
			except:
				self.fail_count+=1
			if self.fail_count>10:
				break

	def start_user(self):
		self.start()

	def stop_user(self):
		self.run_user = False

	def user_status(self):
		if self.is_alive():
			print('Running user')
			print('Total updates:',self.update_count)
			print('Total failed updates:',self.fail_count)
			print('To stop, run: U.stop_user()')
		else:
			print('No running users')
			print('To start, run: U.start_user()')

class Conway(User):
	'''
	Class that simulates a user doing changes to the grid.

	To use, instantiate the class, and run User.start_user().
	This will create a new thread with a user running. 
	'''
	def __init__(self,*args,sleep_time=1,name='Conway',alive_type=None,**kwargs):
		super(Conway, self).__init__(*args,**kwargs)
		self.sleep_time = sleep_time
		self.name = name
		try:
			geos = pd.DataFrame([(cell['properties']['id'],cell['geometry']) for cell in self.get_GEOGRID()['features']],columns=['id','geometry'])
		except:
			geos = pd.DataFrame([(i,cell['geometry']) for i,cell in enumerate(self.get_GEOGRID()['features'])],columns=['id','geometry'])
		geos = gpd.GeoDataFrame(geos.drop('geometry',1),geometry=geos['geometry'].apply(lambda x: shape(x))) # no crs to avoid warning
		geos['lon'] = round(geos.geometry.centroid.x,4)
		geos['lat'] = round(geos.geometry.centroid.y,4)
		M = pd.pivot_table(geos,index=['lat'],values=['id'],columns=['lon'])
		self.M = M.values # matrix with ids
		index_lookup = {}
		for i in range(self.M.shape[0]):
			for j in range(self.M.shape[1]):
				index_lookup[self.M[i,j]] = (i,j)
		self.index_lookup = index_lookup # dict to obtain the i,j index of each cell
		self.alive = list(self.get_GEOGRID()['properties']['types'].keys())[0] if alive_type is None else alive_type
		self.dead  = list([k for k in self.get_GEOGRID()['properties']['types'].keys() if k!=self.alive])[0] 

	def survival(self, x, y, universe):
		"""
		:param x: x coordinate of the cell
		:param y: y coordinate of the cell
		"""
		num_neighbours = np.sum(universe[x - 1:x + 2, y - 1:y + 2]) - universe[x, y]

		if universe[x, y] == 1:
			if num_neighbours < 2 or num_neighbours > 3:
				return 0
			else:
				return 1
		elif universe[x, y] == 0:
			if num_neighbours == 3:
				return 1
			else:
				return 0

	def next_gen(self,X):
		new_X = np.copy(X)
		for i in range(X.shape[0]):
			for j in range(X.shape[1]):
				new_X[i,j] = self.survival(i, j, X)
		X = new_X
		return X

	def game_of_life(self,geogrid_data):
		living_cells = set([cell['id'] for cell in geogrid_data if cell['name']==self.alive])
		X = np.zeros(self.M.shape)
		for c in living_cells:
			X[self.index_lookup[c]] = 1
		X_next = self.next_gen(X)

		living_cells_index = np.where(X_next==1)
		living_cells_next = [self.M[i,j] for i,j in zip(living_cells_index[0],living_cells_index[1])]

		for cell in geogrid_data:
			if cell['id'] in living_cells_next:
				cell['name'] = self.alive
			elif cell['name'] == self.alive:
				cell['name'] = self.dead
		return geogrid_data

	def user_sim(self,quietly=True):
		'''
		Simulates a user that changes the grid every sleep_time seconds.
		The user flips a random cell 90% of the time, and shuffles the whole grid the other 10% of the time. 
		There is a small chance that the user will reset the grid to its original setting. 
		'''
		self.run_user = True
		self.update_count = 0
		self.fail_count = 0
		if not quietly:
			print('Playing game of life with:',self.alive)
		while self.run_user:
			sleep(self.sleep_time)
			try:
				t0 = time.time()
				self.update_geogrid_data(self.game_of_life)
				tf = time.time()
				if not quietly:
					print('Update successful. Runtime:',tf-t0)
				self.update_count+=1
			except:
				self.fail_count+=1
				if not quietly:
					print('Update fail')
			if self.fail_count>10:
				break



def spin_users(table_name,n_users,sleep_time=7):
	'''
	Creates and starts multiple users for testing.

	Parameters
	----------
	table_name: str
		Table to link users to.
	n_users: int
		Number of users to generate.
	'''
	user_objects = []
	for i in range(n_users):
		U = User(table_name, name=f'Simulated user {i}', sleep_time=sleep_time)
		U.start_user()
		user_objects.append(U)
	return user_objects

def stop_users():
	'''
	Stops all running users.
	'''
	for u in User.getinstances():
		u.stop_user()

def start_users():
	'''
	Starts all stopped users.
	'''
	for u in User.getinstances():
		if not u.is_alive():
			u.start_user()

def list_users(verbose=False):
	'''
	Lists all users and their status.
	'''
	n_running_users = 0
	n_users = 0
	update_count = 0
	fail_count = 0
	for u in User.getinstances():
		n_users+=1
		if u.is_alive():
			n_running_users+=1
			update_count+=u.update_count
			fail_count+=u.fail_count
	print(f'{n_users} User instances')
	print(f'{n_running_users} Running users')
	print('Total updates:',update_count)
	print('Total failed updates:',fail_count)

	if verbose:
		for u in User.getinstances():
			if u.is_alive():
				print(f'\t{u.name} Running')
				print(f'\tTotal updates:',u.update_count)
				print(f'\tTotal failed updates:',u.update_count)
			else:
				print(f'\t{u.name} stopped')


