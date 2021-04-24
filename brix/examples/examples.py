from ..classes import Indicator

import random
class RandomIndicator(Indicator):
	def setup(self):
		self.name = 'John Random'
		pass

	def return_indicator(self, geogrid_data):
		result=[{'name': 'Social Wellbeing', 'value': random.random()},
				{'name': 'Environmental Impact', 'value': random.random()},
				{'name': 'Mobility Impact', 'value': random.random()},
				{'name': 'Economic Impact', 'value': random.random()},
				{'name': 'Innovation Potential', 'value': random.random()}]
		return result


import pandas as pd
import json
class ShellIndicator(Indicator):
	'''
	Example of an empty-shell indicator that always returns one.
	'''

	def setup(self):
		self.name = 'John Shell'
		self.fitted_model = None

	def load_module(self):
		self.fitted_model = 1

	def return_indicator(self, geogrid_data):
		return self.fitted_model


from numpy import log
from collections import Counter
class Diversity(Indicator):
	'''
	Example of a diversity of land use indicator
	'''
	def setup(self,viz_type = 'bar'):
		self.name = 'Entropy'
		self.requires_geogrid_props = False
		self.viz_type = viz_type

	def return_indicator(self, geogrid_data):
		uses = [cell['name'] for cell in geogrid_data]
		uses = [use for use in uses if use != 'None']

		frequencies = Counter(uses)
		total = sum(frequencies.values(), 0.0)
		entropy = 0
		for key in frequencies:
			p = frequencies[key]/total
			entropy += -p*log(p)

		entropy = entropy/log(geogrid_data.number_of_types())

		return entropy


from numpy import mean
import random
class Noise(Indicator):
	'''
	Example of Noise heatmap indicator for points centered in each grid cell.
	The main difference between a heatmap and a numeric indicator is that indicator_type is set to either 'heatmap' or 'access'.

	Note that this class requires the geometry of the table as input, which is why it sets:
	requires_geometry = True
	in the setup.

	'''
	def setup(self,name=None):
		self.indicator_type = 'heatmap'
		self.name = ('noise' if name is None else name)
		self.requires_geometry = True

	def load_module(self):
		pass

	def return_indicator(self, geogrid_data):
		features = []
		for cell in geogrid_data:
			feature = {}
			lat,lon = zip(*cell['geometry']['coordinates'][0])
			lat,lon = mean(lat),mean(lon)
			feature['geometry'] = {'coordinates': [lat,lon],'type': 'Point'}
			feature['properties'] = {self.name:random.random()}
			features.append(feature)
		out = {'type':'FeatureCollection','features':features}
		return out


import random
class RandomFlag(Indicator):
	'''
	Example of textual indicator that annotates two random cells with `yes!` and `no!`.
	'''
	def setup(self):
		self.indicator_type = 'textual'
		self.requires_geometry = True
		self.name = 'Yes/No'

	def return_indicator(self, geogrid_data):
		cells = random.sample(geogrid_data,2)
		out = [
			{'id':cells[0]['id'],'info':'yes!'},
			{'id':cells[1]['id'],'info':'no!'},
		]
		return out
