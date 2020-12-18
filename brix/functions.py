# Other functions that use brix objects (e.g. function to get street network for table from OSM)

from .classes import Handler
from .classes import Indicator
from .classes import CompositeIndicator
from .classes import GEOGRIDDATA
from .helpers import get_buffer_size, has_tags

try:
	from osmnx import geometries_from_polygon
except:
	geometries_from_polygon = None
import requests
import pandas as pd
import geopandas as gpd
from geopandas.tools import sjoin

def OSM_infer_geogrid_data(H,amenity_tag_categories=None):
	'''
	Infers the cell type based on the OSM tags classified into categories in amenity_tag_categories.
	This function does not update the color of the cell, as :func:`brix.Handler.post_geogrid_data` will eventually take care of this. 

	Parameters
	----------
	H: :class:`brix.Handler`
		Handler for the table to infer types for.
	amenity_tag_categories: dict 
		Dictionary with categories of amenities. 
		For example:
			{
				"restaurants": {
					"amenity":["restaurant","cafe","fast_food","pub","cafe"],
					"shop":["coffee"]
				},
				"nightlife": {
					"amenity":["bar","pub","biergarten","nightclub"]
				}
			}
		Will add two new columns: "category_restaurants" and "category_nightlife"

	Returns
	-------
	geogrid_data: list
		List of cells to be updated.
	'''
	if amenity_tag_categories is None:
		raise NameError('amenity_tag_categories is required')
	node_data_df = get_OSM_nodes(H,amenity_tag_categories=amenity_tag_categories)
	node_data_df['category'] = None
	for cat in amenity_tag_categories:
	    node_data_df.loc[node_data_df[f'category_{cat}'],'category'] = cat
	node_data_df = node_data_df[~node_data_df['category'].isna()]


	geogrid_df = H.get_geogrid_data(include_geometries=True,as_df=True)
	geogrid_df = gpd.GeoDataFrame(geogrid_df[['id']],geometry=geogrid_df['geometry'])

	matched = sjoin(node_data_df, geogrid_df, how='inner')
	matched = matched[['category','id_right','id_left']].groupby(['id_right','category']).count().reset_index().sort_values(by='id_left',ascending=False).groupby(['id_right','category']).first()
	id_category = dict(matched.reset_index()[['id_right','category']].values)
	geogrid_data = H.get_geogrid_data()
	for cell in geogrid_data:
		if cell['id'] in id_category.keys():
			cell['name'] = id_category[cell['id']] 
	return geogrid_data

def add_height(H, levels):
	'''
	Adds levels to all the cells in geogrid.
	Function mainly used for testing as an example. 

	Parameters
	---------
	H: :class:`brix.Handler`
		Handler connected to the necessarry table. 
	levels: float
		Number of levels by which to rise height

	Returns
	-------
	new_geogrid_data: dict
		Same as input, but with additional levels in each cell.
	'''
	geogrid_data = H.get_geogrid_data()
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

	Returns
	-------
	I: :class:`brix.Indicator`
		Numeric indicator that returns the value of the given function. 
	'''
	I = Indicator(
		name=name,
		requires_geometry=requires_geometry,
		requires_geogrid_props=requires_geogrid_props,
		viz_type=viz_type)
	I.set_return_indicator(return_indicator)
	return I

def get_OSM_geometries(H,tags = {'building':True},buffer_percent=0.25,use_stored=True,only_polygons=True):
	'''
	Gets the buildings from OSM within the table's geogrid.
	This function requires osmnx package to be installed. 
	Simple usage: `buildings = OSM_geometries(H)`.

	Parameters
	----------
	H: :class:`brix.Handler`
		Table Handler.
	tags: dict, defaults to building
		Tags of geometries to get. See: `osmnx.geometries_from_polygon`
	buffer_percent: float, defaults to 0.25
		Buffer to use around the table.
		Size of buffer in units of the grid diameter
		See :func:`brix.get_buffer_size`.
	use_stored: boolean, defaults to True
		If True, the function will retrieve the results once and save them in the Handler under the :attr:`brix.Handler.OSM_data` attribute.
		If False, the function will retrieve the results every time it is called.
	only_polygons: boolean, defaults to True
		If False, it will return all buildings, including those without their polygon shape (e..g some buildings just have a point).
	  
	Returns
	-------
	buildings: geopandas.GeoDataFrame
		Table with geometries from OSM. 
	'''
	if 'OSM_geometries' not in H.OSM_data.keys():
		H.OSM_data['OSM_geometries'] = None
	if (H.OSM_data['OSM_geometries'] is None)|(not use_stored):
		limit = H.grid_bounds(buffer_percent=buffer_percent)
		if geometries_from_polygon is not None:
			buildings = geometries_from_polygon(limit,tags)
		else:
			raise NameError('Package osmnx not found.')
		H.OSM_data['OSM_geometries'] = buildings.copy()
	else:
		print('Using stored OSM geometries')

	buildings = H.OSM_data['OSM_geometries'].copy()
	if only_polygons:
		buildings = buildings[buildings.geometry.type=='Polygon']
	return buildings

def get_OSM_nodes(H,expand_tags=False,amenity_tag_categories=None,use_stored=True,buffer_percent=0.25,quietly=True):
	'''
	Returns the nodes from OSM.
	This function can be used to obtain a list of amenities within the area defined by the table. 
	There is a default buffer added around the grid, but you can increase this by changing `buffer_percent`.

	Parameters
	----------
	H: :class:`brix.Handler`
		Table Handler.
	expand_tags: boolean, defaults to False.
		If True, it will expand all the tags into a wide format with one column per tag.
		Columns will be named as: tag_{tag}
	amenity_tag_categories: dict (optional)
		Dictionary with categories of amenities. 
		For example:
			{
				"restaurants": {
					"amenity":["restaurant","cafe","fast_food","pub","cafe"],
					"shop":["coffee"]
				},
				"nightlife": {
					"amenity":["bar","pub","biergarten","nightclub"]
				}
			}
		Will add two new columns: "category_restaurants" and "category_nightlife"
	use_stored: boolean, defaults to True
		If True, the function will retrieve the results once and save them in the Handler under the :attr:`brix.Handler.OSM_data` attribute.
		If False, the function will retrieve the results every time it is called.
	buffer_percent: float, defaults to 0.25
		Buffer to use around the table.
		Size of buffer in units of the grid diameter
		See `get_buffer_size`.
	quietly: boolean, defaults to False
		If True, it will print the generated URL

	Returns
	-------
	node_data_df: geopandas.GeoDataFrame
		Table with all the nodes within the bounds. 
	'''

	if 'OSM_nodes' not in H.OSM_data.keys():
	    H.OSM_data['OSM_nodes'] = None
	    
	if (H.OSM_data['OSM_nodes'] is None)|(not use_stored):
		bbox = H.grid_bounds(bbox=True,buffer_percent=buffer_percent)
		OSM_NODES_URL_ROOT='https://lz4.overpass-api.de/api/interpreter?data=[out:json][bbox];node;out;&bbox='
		str_bounds=str(bbox[0])+','+str(bbox[1])+','+str(bbox[2])+','+str(bbox[3])
		osm_node_url_bbox=OSM_NODES_URL_ROOT+str_bounds

		if not quietly:
			print(osm_node_url_bbox)
		r = requests.get(osm_node_url_bbox)
		node_data = r.json()
		node_data_df=pd.DataFrame(node_data['elements'])
		H.OSM_data['OSM_nodes'] = node_data_df.copy()
	else:
		print('Using stored OSM data')

	node_data_df = H.OSM_data['OSM_nodes'].copy()

	if amenity_tag_categories is not None:    
		for cat_name in amenity_tag_categories:
			node_data_df[f'category_{cat_name}'] = node_data_df.apply(lambda row: has_tags(row['tags'], amenity_tag_categories[cat_name]), axis=1)

	if expand_tags:
		tag_df = []
		for i,t in node_data_df[~node_data_df['tags'].isna()][['id','tags']].values:
			t = {f'tag_{k}':t[k] for k in t}
			t['id'] = i
			tag_df.append(t)
		tag_df = pd.DataFrame(tag_df)
		node_data_df = pd.merge(node_data_df,tag_df,how='left')

	node_data_df = gpd.GeoDataFrame(node_data_df,geometry=gpd.points_from_xy(node_data_df['lon'],node_data_df['lat']))
	return node_data_df
