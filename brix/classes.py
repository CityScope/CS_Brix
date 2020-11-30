import requests
import webbrowser
import json
import pygeohash as pgh
import joblib
import numpy as np
import pandas as pd
import geopandas as gpd
from warnings import warn
from time import sleep
from collections import defaultdict
from shapely.geometry import shape
from .helpers import is_number
from threading import Thread

class GEOGRIDDATA(list):
	def __init__(self,geogrid_data):
		super(GEOGRIDDATA, self).__init__()
		for e in geogrid_data:
			self.append(e)
		self.geogrid_props = None

	def set_geogrid_props(self,geogrid_props):
		self.geogrid_props = geogrid_props

	def get_geogrid_props(self):
		return self.geogrid_props

class Handler(Thread):
	'''Class to handle the connection for indicators built based on data from the GEOGRID. To use, instantiate the class and use the :func:`~brix.Handler.add_indicator` method to pass it a set of :class:`~brix.Indicator` objects.

	Parameters
	----------
	table_name : str
		Table name to lisen to.
		https://cityio.media.mit.edu/api/table/table_name
	GEOGRIDDATA_varname : str, defaults to `GEOGRIDDATA`
		Name of geogrid-data variable in the table API.
		The object located at:
		https://cityio.media.mit.edu/api/table/table_name/GEOGRIDDATA_varname
		will be used as input for the return_indicator function in each indicator class.
	GEOGRID_varname : str, defaults to `GEOGRID`
		Name of variable with geometries.
	quietly : boolean, defaults to `True`
		If True, it will show the status of every API call.
	reference : dict, optional
		Dictionary for reference values for each indicator.
	'''
	def __init__(self, table_name, 
		GEOGRIDDATA_varname = 'GEOGRIDDATA', 
		GEOGRID_varname = 'GEOGRID', 
		quietly=True, 
		host_mode ='remote' , 
		reference = None):

		super(Handler, self).__init__()

		if host_mode=='local':
			self.host = 'http://127.0.0.1:5000/'
		else:
			self.host = 'https://cityio.media.mit.edu/'
		self.table_name = table_name
		self.quietly = quietly

		self.sleep_time = 0.5
		self.nAttempts = 5
		self.append_on_post = False

		self.front_end_url   = 'https://cityscope.media.mit.edu/CS_cityscopeJS/?cityscope='+self.table_name
		self.cityIO_get_url  = self.host+'api/table/'+self.table_name
		self.cityIO_post_url = self.host+'api/table/update/'+self.table_name
		
		self.GEOGRID_varname = GEOGRID_varname
		self.GEOGRIDDATA_varname = GEOGRIDDATA_varname
		self.GEOGRID = None

		self.indicators = {}
		self.grid_hash_id = None
		self.grid_hash_id = self.get_grid_hash()

		self.previous_indicators = None
		self.previous_access = None

		self.none_character = 0
		self.geogrid_props=None

		self.reference =reference
        
	def check_table(self,return_value=False):
		'''Prints the front end url for the table. 

		Parameters
		----------
		return_value : boolean, defaults to `False`
			If `True` it will print and return the front end url.

		Returns
		-------
		front_end_url : str
			Onlye if `return_value=True`.
		'''
		print(self.front_end_url)
		if return_value:
			return self.front_end_url

	def see_current(self,indicator_type='numeric'):
		'''Returns the current values of the indicators posted for the table.

		Parameters
		----------
		indicator_type : str, defaults to `numeric`
			Type of the indicator. Choose either `numeric`, `access`, or `heatmap` (`access` and `heatmap` refer to the same type).

		Returns
		-------
		current_status: dict
			Current value of selected indicators.
		'''
		if indicator_type in ['numeric']:
			print(self.cityIO_get_url+'/indicators')
			r = self._get_url(self.cityIO_get_url+'/indicators')
		elif indicator_type in ['heatmap','access']:
			print(self.cityIO_get_url+'/access')
			r = self._get_url(self.cityIO_get_url+'/access')
		else:
			raise NameError('Indicator type should either be numeric, heatmap, or access. Current type: '+str(indicator_type))
		if r.status_code==200:
			return r.json()
		else:
			warn('Cant access cityIO hashes')
			return {}

	def list_indicators(self):
		'''Returns list of all indicator names.
		
		Returns
		-------
		indicators_names : list
			List of indicator names.
		'''
		return [name for name in self.indicators]

	def indicator(self,name):
		'''Returns the :class:`brix.Indicator` with the given name.

		Parameters
		----------
		name : str
			Name of the indicator. See :func:`brix.Handler.list_indicators`.

		Returns
		-------
		selected_indicator : :class:`brix.Indicator`
			Selected indicator object.
		'''
		return self.indicators[name]

	def add_indicators(self,indicator_list,test=True):
		'''Same as :func:`brix.Handler.add_indicator` but it takes in a list of :class:`brix.Indicator` objects.

		Parameters
		----------
		indicator_list : list
			List of :class:`brix.Indicator` objects.
		'''
		for I in indicator_list:
			self.add_indicator(I,test=test)

	def add_indicator(self,I,test=True):
		'''Adds indicator to handler object.

		Parameters
		----------
		I : :class:`brix.Indicator`
			Indicator object to handle. If indicator has name, this will use as identifier. If indicator has no name, it will generate an identifier.
		test : boolean, defaults to `True`
			If `True` it will ensure the indicator runs before adding it to the :class:`brix.Handler`. 
		'''
		if not isinstance(I,Indicator):
			raise NameError('Indicator must be instance of Indicator class')
		if I.name is not None:
			indicatorName = I.name
		else:
			indicatorName = ('0000'+str(len(self.indicators)+1))[-4:]

		if I.tableHandler is not None:
			warn(f'Indicator {indicatorName} has a table linked to it. Remember you do not need to link_table when using the Handler class')

		if indicatorName in self.indicators.keys():
			warn(f'Indicator {indicatorName} already exists and will be overwritten')

		self.indicators[indicatorName] = I
		if test:
			geogrid_data = self._get_grid_data()
			if I.indicator_type not in set(['numeric','heatmap','access']):
				raise NameError('Indicator type should either be numeric, heatmap, or access. Current type: '+str(I.indicator_type))
			try:
				if I.is_composite:
					indicator_values = self.get_indicator_values(include_composite=False)
					self._new_value(indicator_values,indicatorName)
				else:
					self._new_value(geogrid_data,indicatorName)
			except:
				warn('Indicator not working: '+indicatorName)

	def return_indicator(self,indicator_name):
		'''Returns the value returned by :func:`brix.Indicator.return_indicator` function of the selected indicator.

		Parameters
		----------
		indicator_name : str
			Name or identifier of the indicator. See :func:`brix.Handler.list_indicators()`

		Returns
		-------
		indicator_value : dict or float
			Result of :func:`brix.Indicator.return_indicator` function for the selected indicator.
		'''
		geogrid_data = self._get_grid_data()
		I = self.indicators[indicator_name]
		if I.is_composite:
			indicator_values = self.get_indicator_values(include_composite=False)
			return I.return_indicator(indicator_values)
		else:
			return I.return_indicator(geogrid_data)

	def _format_geojson(self,new_value):
		'''
		Formats the result of the return_indicator function into a valid geojson (not a cityIO geojson)
		'''
		if isinstance(new_value,dict) and ('properties' in new_value.keys()) and ('features' in new_value.keys()):
			if (len(new_value['properties'])==1) and all([((not isinstance(f['properties'],dict))) and (is_number(f['properties'])) for f in new_value['features']]):
				# print('Type1B')
				for f in new_value['features']:
					f['properties'] = [f['properties']]
			else:
				# print('Type1')
				pass
			if all([(not isinstance(f['properties'],dict)) for f in new_value['features']]):
				for f in new_value['features']:
					feature_properties = f['properties']
					if len(feature_properties)<len(new_value['properties']):
						feature_properties+=[self.none_character]*(len(new_value['properties'])-len(feature_properties))
					elif len(feature_properties)>len(new_value['properties']):
						feature_properties = feature_properties[:new_value['properties']]
					f['properties'] = dict(zip(new_value['properties'],feature_properties))
			new_value.pop('properties')

		elif isinstance(new_value,dict) and ('features' in new_value.keys()):
			if all([(not isinstance(f['properties'],dict)) and isinstance(f['properties'],list) and (len(f['properties'])==1) for f in new_value['features']]):
				# print('Type2B')
				for f in new_value['features']:
					f['properties'] = {indicator_name:f['properties'][0]}
			elif all([(not isinstance(f['properties'],dict)) and is_number(f['properties']) for f in new_value['features']]):
				# print('Type2C')
				for f in new_value['features']:
					f['properties'] = {indicator_name:f['properties']}
			else:
				# print('Type2')
				pass

		elif isinstance(new_value,list) and all([(isinstance(f,dict) and 'geometry' in f.keys()) for f in new_value]):
			if all([is_number(f['properties']) for f in new_value]):
				# print('Type3B')
				for f in new_value:
					f['properties'] = {indicator_name:f['properties']}
			elif not all([isinstance(f['properties'],dict) for f in new_value]):
				raise NameError('Indicator returned invalid geojson or feature list:'+indicator_name)
			else:
				# print('Type3')
				pass
			new_value = {'features':new_value,'type':'FeatureCollection'}
		else:
			raise NameError('Indicator returned invalid geojson or feature list:'+indicator_name)

		for feature in new_value['features']:
			feature['properties'] = defaultdict(lambda: self.none_character,feature['properties'])
		return new_value

	def _new_value(self,geogrid_data,indicator_name):
		'''
		Formats the result of the indicator's return_indicator function.a

		If indicator is numeric, the result is formatted as:
			[
				{
					'name':xxx, 
					'indicator_type':yyy, 
					'viz_type':zzz, 
					'value':value
				},
				{
					...
				},
				...
			]
		If indicator is access or heatmap, the result is formatted as a list of features:
			[
				feature1,
				feature2,
				...
			]
		with each feature formatted as:
			{
				'geometry':{
								...
							},
				'properties':{
								name: value,
								...
				}
			}
		'''
		I = self.indicators[indicator_name]

		if I.indicator_type in ['access','heatmap']:
			new_value = I.return_indicator(geogrid_data)
			new_value = self._format_geojson(new_value)
			return [new_value]
		elif I.indicator_type in ['numeric']:
			new_value = I.return_indicator(geogrid_data)
			if isinstance(new_value,list)|isinstance(new_value,tuple):
				for i in range(len(new_value)):
					val = new_value[i]
					if not isinstance(val,dict):
						try:
							json.dumps(val)
							new_value[i] = {'value':val}
						except:
							warn('Indicator return invalid type:'+str(indicator_name))
					if ('indicator_type' not in val.keys())&(I.indicator_type is not None):
						val['indicator_type'] = I.indicator_type
					if ('viz_type' not in val.keys())&(I.viz_type is not None):
						val['viz_type'] = I.viz_type
				return list(new_value)
			else:
				if not isinstance(new_value,dict):
					try:
						json.dumps(new_value)
						new_value = {'value':new_value}
					except:
						warn('Indicator return invalid type:'+str(indicator_name))
				if ('name' not in new_value.keys()):
					new_value['name'] = indicator_name
				if ('indicator_type' not in new_value.keys())&(I.indicator_type is not None):
					new_value['indicator_type'] = I.indicator_type
				if ('viz_type' not in new_value.keys())&(I.viz_type is not None):
					new_value['viz_type'] = I.viz_type
				print(new_value)
				return [new_value]


	def _combine_heatmap_values(self,new_values_heatmap):
		'''
		Combines a list of heatmap features (formatted as geojsons) into one cityIO GeoJson
		'''

		all_properties = set([])
		combined_features = {}
		for new_value in new_values_heatmap:
			for f in new_value['features']:
				if f['geometry']['type']=='Point':
					all_properties = all_properties|set(f['properties'].keys())
					lon,lat = f['geometry']['coordinates']
					hashed = pgh.encode(lat,lon)
					
					if hashed in combined_features.keys():
						combined_features[hashed]['properties'] = {**combined_features[hashed]['properties'], **f['properties']} 
						combined_features[hashed]['properties'] = defaultdict(lambda: self.none_character,combined_features[hashed]['properties'])
					else:
						combined_features[pgh.encode(lat,lon)] = f
				else:
					raise NameError('Only Points supported at this point')
		all_properties = list(all_properties)
		combined_features = list(combined_features.values())
		for f in combined_features:
			f['properties'] = [f['properties'][p] for p in all_properties]

		return {'type':'FeatureCollection','properties':all_properties,'features':combined_features}

	def get_indicator_values(self,include_composite=False):
		'''
		Returns the current values of numeric indicators. Used for developing a composite indicator.

		Parameters
		----------
		include_composite : boolean, defaults to `False`
			If `True` it will also include the composite indicators, using the :class:`brix.Indicator` `is_composite` parameter. 

		Returns
		-------
		indicator_values : dict
			Dictionary with values for each indicator formatted as: ``{indicator_name: indicator_value, ...}``
		'''
		geogrid_data = self.get_geogrid_data()
		new_values_numeric = []
		for indicator_name in self.indicators:
			I = self.indicators[indicator_name]
			if (I.indicator_type not in ['access','heatmap'])&(not I.is_composite):
				new_values_numeric += self._new_value(geogrid_data,indicator_name)
		indicator_values = {i['name']:i['value'] for i in new_values_numeric}
		if include_composite:
			for indicator_name in self.indicators:
				I = self.indicators[indicator_name]
				if (I.indicator_type not in ['access','heatmap'])&(I.is_composite):
					new_values_numeric += self._new_value(indicator_values,indicator_name)
		indicator_values = {i['name']:i['value'] for i in new_values_numeric}
		return indicator_values

	def update_package(self,geogrid_data=None,append=False):
		'''
		Returns the package that will be posted in CityIO.

		Parameters
		----------
		geogrid_data : dict, optional
			Result of :func:`brix.Handler.get_geogrid_data`. If not provided, it will be retrieved. 
		append : boolean, defaults to `False`
			If True, it will append the new indicators to whatever is already there.

		Returns
		-------
		new_values : list
			Note that all heatmat indicators have been grouped into just one value.
		'''
		if geogrid_data is None:
			geogrid_data = self._get_grid_data()
		new_values_numeric = []
		new_values_heatmap = []

		for indicator_name in self.indicators:
			try:
				I = self.indicators[indicator_name]
				if I.indicator_type in ['access','heatmap']:
					new_values_heatmap += self._new_value(geogrid_data,indicator_name)
				elif not I.is_composite:
					new_values_numeric += self._new_value(geogrid_data,indicator_name)
			except:
				warn('Indicator not working:'+str(indicator_name))

		for indicator_name in self.indicators:
			I = self.indicators[indicator_name]
			if (I.is_composite)&(I.indicator_type not in ['access','heatmap']):
				indicator_values = {i['name']:i['value'] for i in new_values_numeric}
				new_values_numeric += self._new_value(indicator_values,indicator_name)

		# add ref values if they exist
		if self.reference is not None:
			for new_value in new_values_numeric:
				if new_value['name'] in self.reference:
					new_value['ref_value']=self.reference[new_value['name']]
		
		if append:
			if len(new_values_numeric)!=0:
				current = self.see_current()
				self.previous_indicators = current
				current = [indicator for indicator in current if indicator['name'] not in self.indicators.keys()]
				new_values_numeric += current

			if len(new_values_heatmap)!=0:
				current_access = self.see_current(indicator_type='access')
				self.previous_access = current_access
				current_access = self._format_geojson(current_access)
				new_values_heatmap = [current_access]+new_values_heatmap

		new_values_heatmap = self._combine_heatmap_values(new_values_heatmap)
		return {'numeric':new_values_numeric,'heatmap':new_values_heatmap}
		
	def test_indicators(self):
		'''Dry run over all indicators.'''
		geogrid_data = self._get_grid_data()
		for indicator_name in self.indicators:
			if self.indicators[indicator_name].is_composite:
				indicator_values = self.get_indicator_values(include_composite=False)
				self._new_value(indicator_values,indicator_name)
			else:
				self._new_value(geogrid_data,indicator_name)
            
	def get_geogrid_props(self):
		'''
		Gets the `GEOGRID` properties defined for the table. These properties are not dynamic and include things such as the NAICS and LBCS composition of each lego type.

		Returns
		-------
		geogrid_props : dict
			Table GEOGRID properties.
		'''
		if self.geogrid_props is None:
			r = self._get_url(self.cityIO_get_url+'/GEOGRID/properties')
			if r.status_code==200:
				self.geogrid_props = r.json()
			else:
				warn('Cant access cityIO type definitions')
				sleep(1)
		return self.geogrid_props

	def get_table_properties(self):
		'''
		Gets table properties. This info can also be accessed through :func:`brix.Handler.get_geogrid_props`.
		'''
		return self.get_geogrid_props()['header']

	def get_grid_hash(self):
		'''
		Retreives the GEOGRID hash from:
		http://cityio.media.mit.edu/api/table/table_name/meta/hashes
		'''
		r = self._get_url(self.cityIO_get_url+'/meta/hashes')
		if r.status_code==200:
			hashes = r.json()
			try:
				grid_hash_id = hashes[self.GEOGRIDDATA_varname]
			except:
				warn('WARNING: Table does not have a '+self.GEOGRIDDATA_varname+' variable.')
				grid_hash_id = self.grid_hash_id
		else:
			warn('Cant access cityIO hashes')
			sleep(1)
			grid_hash_id=self.grid_hash_id
		return grid_hash_id

	def _get_grid_data(self,include_geometries=False,with_properties=False):
		r = self._get_url(self.cityIO_get_url+'/'+self.GEOGRIDDATA_varname)
		if r.status_code==200:
			geogrid_data = r.json()
		else:
			warn('WARNING: Cant access GEOGRID data')
			sleep(1)
			geogrid_data = None
	
		if include_geometries|any([I.requires_geometry for I in self.indicators.values()]):
			if self.GEOGRID is None:
				r = self._get_url(self.cityIO_get_url+'/'+self.GEOGRID_varname)
				if r.status_code==200:
					geogrid = r.json()
					self.GEOGRID = geogrid
				else:
					warn('WARNING: Cant access GEOGRID data')
			for i in range(len(geogrid_data)):
				geogrid_data[i]['geometry'] = self.GEOGRID['features'][i]['geometry']

		if with_properties|any([I.requires_geogrid_props for I in self.indicators.values()]):
			geogrid_props = self.get_geogrid_props()
			types_def = geogrid_props['types'].copy()
			if 'static_types' in geogrid_props:
				types_def.update(geogrid_props['static_types'])
			types_def['None'] = None
			for cell in geogrid_data:
				cell['properties'] = types_def[cell['name']]
		geogrid_data = GEOGRIDDATA(geogrid_data)
		geogrid_data.set_geogrid_props(self.get_geogrid_props())
		return geogrid_data

	def _get_url(self,url,params=None):
		attempts = 0
		success = False
		while (attempts < self.nAttempts)&(not success):
			if not self.quietly:
				print(url,'Attempt:',attempts)
			r = requests.get(url,params=params)
			if r.status_code==200:
				success=True
			else:
				attempts+=1
		if not success:
			warn('FAILED TO RETRIEVE URL: '+url)
		return r

	def get_geogrid_data(self,include_geometries=False,with_properties=False,as_df=False):
		'''
		Returns the geogrid data from:
		http://cityio.media.mit.edu/api/table/table_name/GEOGRIDDATA

		Parameters
		----------
		include_geometries : boolean, defaults to `False`
			If `True` it will also add the geometry information for each grid unit.
		with_properties : boolean, defaults to `False`
			If `True` it will add the properties of each grid unit as defined when the table was constructed (e.g. LBCS code, NAICS code, etc.)
		as_df: boolean, defaults to `False`
			If `True` it will return data as a pandas.DataFrame.

		Returns
		-------
		geogrid_data : dict
			Data taken directly from the table to be used as input for :class:`brix.Indicator.return_indicator`.
		'''
		geogrid_data = self._get_grid_data(include_geometries=include_geometries,with_properties=with_properties)
		if as_df:
			for cell in geogrid_data:
				if 'properties' in cell.keys():
					cell_props = cell['properties']
					for k in cell_props:
						cell[f'property_{k}'] = cell_props[k]
					del cell['properties']
			geogrid_data = pd.DataFrame(geogrid_data)
			if include_geometries:
				geogrid_data = gpd.GeoDataFrame(geogrid_data.drop('geometry',1),geometry=geogrid_data['geometry'].apply(lambda x: shape(x)))
		return geogrid_data

	def perform_update(self,grid_hash_id=None,append=True):
		'''
		Performs single table update.

		Parameters
		----------
		grid_hash_id : str, optional
			Current grid hash id. If not provided, it will retrieve it.
		append : boolean, defaults to `True`
			If `True`, it will append the new indicators to whatever is already there.
		'''
		if grid_hash_id is None: 
			grid_hash_id = self.get_grid_hash()	
		geogrid_data = self._get_grid_data()
		if not self.quietly:
			print('Updating table with hash:',grid_hash_id)

		new_values = self.update_package(geogrid_data=geogrid_data,append=append)

		if len(new_values['numeric'])!=0:
			r = requests.post(self.cityIO_post_url+'/indicators', data = json.dumps(new_values['numeric']))

		if len(new_values['heatmap']['features'])!=0:
			r = requests.post(self.cityIO_post_url+'/access', data = json.dumps(new_values['heatmap']))
		if not self.quietly:
			print('Done with update')
		self.grid_hash_id = grid_hash_id

	def rollback(self):
		''':class:`brix.Handler` keeps track of the previous value of the indicators and access values.This function rollsback the current values to whatever the locally stored values are.
		See also :func:`brix.Handler.previous_indicators` and :func:`brix.Handler.previous_access`.
		'''
		r = requests.post(self.cityIO_post_url+'/indicators', data = json.dumps(self.previous_indicators))
		r = requests.post(self.cityIO_post_url+'/access', data = json.dumps(self.previous_access))

	def clear_table(self):
		'''Clears all indicators from the table.'''
		grid_hash_id = self.get_grid_hash()
		empty_update = {'numeric': [],'heatmap': {'type': 'FeatureCollection', 'properties': [], 'features': []}}
		r = requests.post(self.cityIO_post_url+'/indicators', data = json.dumps(empty_update['numeric']))
		r = requests.post(self.cityIO_post_url+'/access', data = json.dumps(empty_update['heatmap']))
		if not self.quietly:
			print('Cleared table')
		self.grid_hash_id = grid_hash_id

	def _listen(self,showFront=True):
		'''
		Lower level listen. Should only be called directly for debugging purposes. 
		Use :func:`brix.Handler.listen` instead.

		Listens for changes in the table's geogrid and update all indicators accordingly. 
		You can use the update_package method to see the object that will be posted to the table.
		This method starts with an update before listening.

		Parameters
		----------
		showFront : boolean, defaults to `True`
			If `True` it will open the front-end URL in a webbrowser at start.
		'''
		if not self.quietly:
			print('Table URL:',self.front_end_url)
			print('Testing indicators')
		self.test_indicators()

		if not self.quietly:
			print('Performing initial update')
			print('Update package example:')
			print(self.update_package())
		self.perform_update(append=self.append_on_post)

		if showFront:
			webbrowser.open(self.front_end_url, new=2)
		while True:
			sleep(self.sleep_time)
			grid_hash_id = self.get_grid_hash()
			if grid_hash_id!=self.grid_hash_id:
				self.perform_update(grid_hash_id=grid_hash_id,append=self.append_on_post)

	def run(self):
		'''
		Run method to be called by :func:`threading.Thread.start`. 
		It runs :func:`brix.Handler._listen`.
		'''
		self._listen(showFront=False)

	def listen(self,new_thread=False,showFront=True,append=False):
		'''
		Listens for changes in the table's geogrid and update all indicators accordingly. 
		You can use the update_package method to see the object that will be posted to the table.
		This method starts with an update before listening.
		This runs in a separate thread by default.

		Parameters
		----------
		new_thread : boolean, defaults to `False`.
			If `True` it will run in a separate thread, freeing up the main thread for other tables.
			We recommend setting this to `False` when debugging, to avoid needing to recreate the object. 
		showFront : boolean, defaults to `True`
			If `True` it will open the front-end URL in a webbrowser at start.
			Only works if `new_tread=False`.
		append : boolean, defaults to `False`
			If `True` it will append the new indicators to whatever is already there.
			This option will be deprecated soon. We recommend not using it unless strictly necessary.
		'''
		self.append_on_post = append
		if new_thread:
			self.start()
		else:
			self._listen(showFront=showFront)


class Indicator:
	'''Parent class to build indicators from. To use, you need to define a subclass than inherets properties from this class. Doing so, ensures your indicator inherets the necessary methods and properties to connect with a CityScipe table.'''
	def __init__(self,*args,**kwargs):
		self.name = None
		self.indicator_type = 'numeric'
		self.viz_type = 'radar'
		self.requires_geometry = None
		self.requires_geogrid_props = False
		self.model_path = None
		self.pickled_model = None
		# self.int_types_def=None
		# self.types_def=None
		# self.geogrid_header=None
		self.is_composite = False
		self.tableHandler = None
		self.table_name = None
		for k in ['name','model_path','requires_geometry','indicator_type','viz_type','requires_geogrid_props']:
			if k in kwargs.keys():
				self.name = kwargs[k]
		if self.indicator_type in ['heatmap','access']:
			self.viz_type = None
		self.setup(*args,**kwargs)
		self.load_module()
		if (self.requires_geometry is None):
			if (self.indicator_type in ['heatmap','access']):
				self.requires_geometry = True
			else:
				self.requires_geometry = False


	def setup(self):
		'''User defined function. Used to set up the main attributed of the custom indicator. Acts similar to an `__init__` method.'''
		pass

	def return_indicator(self,geogrid_data):
		'''User defined function. This function defines the value of the indicator as a function of the table state passed as `geogrid_data`. Function must return either a dictionary, a list, or a number. When returning a dict follow the format: ``{'name': 'Indicator_NAME', 'value': 1.00}``. 

		Parameters
		----------
		geogrid_data : dict
			Current state of the table. See :func:`brix.Indicator.get_geogrid_data` and :func:`brix.Handler.get_geogrid_data`. The content of this object will depend on the needs of the indicator. In particular, the values of :attr:`brix.Indicator.requires_geometry` and :attr:`brix.Indicator.requires_geogrid_props`.

		Returns
		-------
		indicator_value : list, dict, or float
			Value of indicator or list of values. When returning a dict, please use the format ``{'name': 'Indicator Name', 'value': indicator_value}``. When returning a list, please return a list of dictionaries in the same format. 
		'''
		return {}


	def load_module(self):
		'''User defined function. Used to load any data necessary for the indicator to run. In principle, you could do everything using :func:`brix.Indicator.setup` but we encourage to separte data loading and module definition into two functions.'''
		if self.model_path is not None:
			self.pickled_model = joblib.load(self.model_path)
			if self.name is None:
				self.name = self.model_path.split('/')[-1].split('.')[0]

	def return_baseline(self,geogrid_data):
		'''User defined function. Used to return a baseline value.
		[This function might get deprecated]
		'''
		return None


	def _transform_geogrid_data_to_df(self,geogrid_data):
		'''
		Transform the geogrid_data to a DataFrame to be used by a pickled model.
		'''
		geogrid_data = pd.DataFrame(geogrid_data)
		if 'geometry' in geogrid_data.columns:
			geogrid_data = gpd.GeoDataFrame(geogrid_data.drop('geometry',1),geometry=geogrid_data['geometry'].apply(lambda x: shape(x)))
		return geogrid_data

	def link_table(self,table_name):
		'''
		Creates a :class:`brix.Handler` and links the table to the indicator. This function should be used only for developing the indicator. 

		Parameters
		----------
		table_name: str or :class:`brix.Handler`
			Name of the table or Handler object.
		'''
		if (table_name is None) & (self.table_name is None):
			raise NameError('Please provide a table_name to link')
		if table_name is None:
			table_name = self.table_name
		if isinstance(table_name,Handler):
			self.tableHandler = table_name
		else:
			self.tableHandler = Handler(table_name)

	def get_table_properties(self):
		'''Gets table properties from the linked table. See :func:`brix.Indicator.link_table` and :func:`brix.Handler.get_table_properties`.'''
		if (self.tableHandler is None)& (self.table_name is None):
			raise NameError('No table linked: use Indicator.link_table(table_name)')
		elif (self.tableHandler is None)& (self.table_name is not None):
			self.tableHandler = Handler(table_name)
		return self.tableHandler.get_geogrid_props()['header']


	def get_geogrid_data(self,as_df=False,include_geometries=None,with_properties=None):
		'''
		Returns the geogrid data from the linked table. Function mainly used for development. See :func:`brix.Indicator.link_table`. It returns the exact object that will be passed to return_indicator


		Parameters
		----------
		as_df: boolean, defaults to `False`
			If `True` it will return data as a pandas.DataFrame.
		include_geometries: boolean, defaults to :attr:`brix.Indicator.requires_geometry`
			If `True`, it will override the default parameter of the Indicator.
		with_properties: boolean, defaults to :attr:`brix.Indicator.requires_geogrid_props`
			If `True`, it will override the default parameter of the Indicator.

		Returns
		-------
		geogrid_data : str or pandas.DataFrame
			Data that will be passed to the :func:`brix.Indicator.return_indicator` function by the :class:`brix.Handler` when deployed.
		'''
		include_geometries = self.requires_geometry if include_geometries is None else include_geometries
		with_properties    = self.requires_geogrid_props if with_properties is None else with_properties
		if self.tableHandler is None:
			if self.table_name is not None:
				self.link_table(table_name=self.table_name)
			else:
				warn('To use this function, please link a table first:\n> Indicator.link_table(table_name)')
				return None

		geogrid_data = self.tableHandler._get_grid_data(include_geometries=include_geometries,with_properties=with_properties)
		if as_df:
			geogrid_data = pd.DataFrame(geogrid_data)
			if include_geometries:
				geogrid_data = gpd.GeoDataFrame(geogrid_data.drop('geometry',1),geometry=geogrid_data['geometry'].apply(lambda x: shape(x)))
		return geogrid_data


class CompositeIndicator(Indicator):
	'''Subclass used to define composite indicators. Composite indicators are functions of already defined indicators. By defining :func:`brix.Indicator.setup` and :func:`brix.Indicator.return_indicator`, this class allows you to define a composite indicator by just passing an aggregation function.'''
	def setup(self,compose_function,selected_indicators=[],*args,**kwargs):
		'''Indicator setup. This function is called upon `__init__` so user does not need to call it independently.

		Parameters
		----------
		compose_function : function
			Function to aggregate values of selected indicators. The function should be build to accept a dictionary with indicator values. See :func:`brix.Handler.get_indicator_values`. 
		selected_indicators : list, optional
			List of indicators to use to aggregate. 
		'''
		self.compose_function = compose_function
		self.is_composite = True
		self.selected_indicators = selected_indicators

	def return_indicator(self, indicator_values):
		'''Applies :attr:`brix.CompositeIndicator.compose_function` to the indicator values to return the composite indicator. 

		Parameters
		----------
		indicator_values : dict
			Dictionary with indicator values. See :func:`brix.Handler.get_indicator_values`. 

		Returns
		-------
		indicator_values : list
			List of one indicator.
		'''
		if len(self.selected_indicators)!=0:
			indicator_values = {k:indicator_values[k] for k in indicator_values if k in self.selected_indicators}
		try:
			value = self.compose_function(indicator_values)
		except:
			indicator_values = np.array([v for v in indicator_values.values()])
			value = self.compose_function(indicator_values)
		return [{'name': self.name, 'value': float(value), 'raw_value': None,'units': None,'viz_type': self.viz_type}]

