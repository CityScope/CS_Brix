# Other functions that use brix objects (e.g. function to get street network for table from OSM)

from .classes import Handler
from .classes import Indicator
from .classes import CompositeIndicator
from .classes import GEOGRIDDATA
from .classes import StaticHeatmap
from .helpers import get_buffer_size, has_tags

try:
	from osmnx import geometries_from_polygon
except:
	geometries_from_polygon = None
import requests
import pandas as pd
import geopandas as gpd
import numpy as np
from geopandas.tools import sjoin
from shapely.geometry import Point


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
	Function that constructs an indicator based on a user defined return_indicator function. 

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

def make_static_heatmap_indicator(shapefile,columns=None,name=None):
	'''
	Function that constructs a heatmap indicator that only visualizes the given shapefile.
	This function wraps :class:`brix.StaticHeatmap` to make it easier for users to find.

	Parameters
	----------
	shapefile: geopandas.GeoDataFrame or str
		Shapefile with values for each point, or path to shapefile.
	columns: list
		Columns to plot. If not provided, it will return all numeric columns.
		The name of the indicator will be given by the name of the column.
	name: str, optional
		Name of the indicator.
		If not provided, it will generate a name by hashing the column names.

	Returns
	-------
	Heatmap: brix.Indicator
		Heatmap indicator that posts the given shapefile to the table.
	'''
	HM = StaticHeatmap(shapefile,columns=columns,name=name)
	return HM

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

def griddify(geogrid_data,shapefile,extend_grid=True,buffer_percent=1.3,columns=None,local_crs=None):
	'''
	From a shapefile with polygons and properties, it creates a shapefile with points and the properties of the polygons they fall in.
	Points are taken from the given GEOGRID and the grid is extended to incorporate a buffer. 
	Points are in the center of the grid.

	Parameters
	----------
	geogrid_data: brix.GEOGRIDDATA

	shapefile: geopandas.GeoDataFrame
		Shapefile in WGS84 (default) or in local_crs (if local_crs is provided)
	extend_grid: boolean, defaults to `True`
		If False, it will only return the values for the centroids of the grid.
	buffer_percent: float, defaults to 1.3
		Buffer to extend the grid by (in units of grid diameter). 
	columns: list, defaults to all numeric
		Columns to select besides geometry. If not provided, it will default to all numeric columns.
	local_crs: str, defaults to wgs84
		ESRI code for local CRS, must match crs of shapefile.
		Recommended: Calculating the centroids of each cell will be more precise if this is provided.

	Returns
	-------
	joined: geopandas.GeoDataFrame
		Shapefile of points and their values.
	'''
	if columns is None:
		columns = shapefile.drop('geometry',1).select_dtypes(include=[np.number]).columns.tolist()

	geogrid_data_df = geogrid_data.as_df(include_geometries=True)
	if local_crs is not None:
		geogrid_data_df = geogrid_data_df.to_crs(local_crs)
	geogrid_data_df.geometry = geogrid_data_df.geometry.centroid

	if extend_grid:
		limit = geogrid_data.bounds(buffer_percent=buffer_percent)
		selected_shapefile = shapefile[shapefile.geometry.within(limit)]

		geogrid_data_df['lat'] = geogrid_data_df.geometry.y
		geogrid_data_df['lon'] = geogrid_data_df.geometry.x
		lon_dx = geogrid_data_df.sort_values(by='lat')['lon'].diff().abs().median()
		lat_dx = geogrid_data_df.sort_values(by='lon')['lat'].diff().abs().median()

		s_lon_min,s_lat_min,s_lon_max,s_lat_max = selected_shapefile.total_bounds
		lat_min = geogrid_data_df['lat'].min()
		lat_max = geogrid_data_df['lat'].max()
		lon_min = geogrid_data_df['lon'].min()
		lon_max = geogrid_data_df['lon'].max()
		all_lats = np.arange(lat_min,s_lat_min,-1*lat_dx).tolist()[::-1][:-1]+np.arange(lat_min,lat_max,lat_dx).tolist()+np.arange(lat_max,s_lat_max,lat_dx).tolist()[1:]
		all_lons = np.arange(lon_min,s_lon_min,-1*lon_dx).tolist()[::-1][:-1]+np.arange(lon_min,lon_max,lon_dx).tolist()+np.arange(lon_max,s_lon_max,lon_dx).tolist()[1:]

		extended_grid = [Point(lon,lat) for lat in all_lats for lon in all_lons]
		extended_grid = gpd.GeoDataFrame([],geometry=extended_grid,crs='EPSG:4326').reset_index().rename(columns={'index':'extended_id'})
		grid_match = sjoin(geogrid_data.as_df(include_geometries=True),extended_grid)
		extended_grid = pd.merge(extended_grid,grid_match[['id','extended_id']].rename(columns={'id':'grid_id'}),how='left')
		selected_grid = extended_grid
		grid_ids = ['extended_id','grid_id']
	else:
		limit = geogrid_data.bounds()
		selected_shapefile = shapefile[shapefile.geometry.within(limit)]
		selected_grid = geogrid_data_df.rename(columns={'id':'grid_id'})
		grid_ids = ['grid_id']

	joined = sjoin(selected_shapefile,selected_grid,how='left')
	joined = pd.merge(joined[grid_ids+columns],selected_grid[grid_ids+['geometry']],how='outer')
	for c in columns:
		joined[c] = joined[c].astype(float)
	joined = joined[~joined['geometry'].isna()]
	joined = joined[~joined[columns].isnull().all(axis=1)] # Drops rows with all null values
	joined = gpd.GeoDataFrame(joined.drop('geometry',1),geometry=joined['geometry'])
	return joined