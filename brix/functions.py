# Other functions that use brix objects (e.g. function to get street network for table from OSM)

from .classes import Handler
from .classes import Indicator
from .classes import CompositeIndicator
from .classes import GEOGRIDDATA
from .helpers import get_buffer_size

import osmnx as ox
from shapely.ops import unary_union
from shapely.geometry import shape

def add_height(geogrid_data, levels):
	'''
	Adds levels to all the cells in geogrid.
	Function mainly used for testing as an example. 

	Parameters
	---------
	geogrid_data: dict or :class:`brix.GEOGRIDDATA`
		List of dicts with the geogrid_data information.
	levels: float
		Number of levels by which to rise height

	Returns
	-------
	new_geogrid_data: dict
		Same as input, but with additional levels in each cell.
	'''
	for cell in geogrid_data:
		cell['height'] += levels
	return geogrid_data

def make_numeric_indicator(name,return_indicator,viz_type='bar',requires_geometry=False,requires_geogrid_props=False):
	'''
	Function that constructs and indicator based on a user defined return_indicator function. 

	Parameters
	----------
	name: str
		Name of the indicator.
	return_indicator: func
		Function that takes in geogrid_data and return the value of the indicator.
	viz_type: str, defaults to 'bar'
		Visualization type in front end. Used for numeric indicators.
	requires_geometry: boolean, defaults to `False`
		If `True`, the geogrid_data object will also come with geometries.
	requires_geogrid_props: boolean, defaults to `False`
		If `True`, the geogrid_data object will include properties. 
	'''
	I = Indicator(
		name=name,
		requires_geometry=requires_geometry,
		requires_geogrid_props=requires_geogrid_props,
		viz_type=viz_type)
	I.set_return_indicator(return_indicator)
	return I

def OSM_geometries(H,tags = {'building':True},buffer_percent=0.25,use_stored=True):
	'''
	Gets the buildings from OSM within the table's geogrid.
	Simple usage: `buildings = OSM_geometries(H)

	Parameters
	----------
	H: :class:`brix.Handler`
		Table Handler.
	tags: dict, defaults to building
		Tags og geometries to get. See: `osmnx.geometries_from_polygon`
	buffer_percent: float, defaults to 0.25
		Buffer to use around the table.
		Size of buffer in units of the grid diameter
		See `get_buffer_size`.
	use_stored: boolean, defaults to True
		If True, the function will retrieve the results once and save them in the Handler under the :attr:`brix.Handler.OSM_data` attribute.
		If False, the function will retrieve the results every time it is called.
	  
	Returns
	-------
	buildings: geopandas.GeoDataFrame
		Table with geometries from OSM. 
	'''
	if 'OSM_geometries' not in H.OSM_data.keys():
		H.OSM_data['OSM_geometries'] = None
	if (H.OSM_data['OSM_geometries'] is None)|(not use_stored):
		geogrid_data = H.get_geogrid_data(include_geometries=True)

		grid = [shape(cell['geometry']) for cell in geogrid_data]
		limit = unary_union(grid)
		buffer_size = get_buffer_size(limit,buffer_percent=0.25)
		limit = limit.buffer(buffer_size)
		limit = limit.simplify(0.001)

		buildings = ox.geometries_from_polygon(limit,tags)
		H.OSM_data['OSM_geometries'] = buildings

	return H.OSM_data['OSM_geometries']