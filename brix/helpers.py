# Helper functions live here
import json
import geopandas as gpd
from warnings import warn
from datetime import datetime
import math

try: # libraries needed to set the timezone of the table
	from timezonefinder import TimezoneFinder
	from pytz import timezone, utc
except:
	warn('timezonefinder and pytz not found')

def deg_to_rad(deg):
	return deg*math.pi/180

def rad_to_deg(rad):
	return rad*180/math.pi

def urljoin(*args,trailing_slash=True):
	trailing_slash_char = '/' if trailing_slash else ''
	return "/".join(map(lambda x: str(x).strip('/'), args)) + trailing_slash_char

def is_number(s):
	'''
	Returns True if input can be turned into a number, else Fals
	'''
	try:
		float(s)
		return True
	except:
		return False

def hex_to_rgb(h):
	return list(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_timezone_offset(lat, lng):
	"""
	returns a location's time zone offset from UTC in hours.
	"""
	today = datetime.now()
	tf = TimezoneFinder()
	tz_target = timezone(tf.certain_timezone_at(lng=lng, lat=lat))
	today_target = tz_target.localize(today)
	today_utc = utc.localize(today)
	return (today_utc - today_target).total_seconds() / 3600

def get_buffer_size(poly,buffer_percent=0.25):
	'''
	Calculates and appropriate buffer size based on the size of the table.

	Parameters
	----------
	poly: shapely.Polygon
		Polygon to calculate buffer for
	buffer_percent: float, defaults to 0.25
		Size of buffer in units of the grid diameter
	  
	Returns
	-------
	buffer_size: float
		Size in units of the coordinates of poly. 
	'''
	lats,lons = zip(*[(lat,lon) for lat,lon in poly.exterior.coords])
	lat_range = abs(max(lats)-min(lats))
	lon_range = abs(max(lons)-min(lons))
	buffer_size = buffer_percent*max(lat_range,lon_range)
	return buffer_size

def has_tags(tags, target_tags):
	'''
	Helper function used by get_OSM_nodes. 
	Checks if tags of the form:
	tag = {
		'amenity':'pub',
		'height':'2.5'
	}

	Belongs to the category defined as:
	target_tags = {
		"amenity":["restaurant","cafe","fast_food","pub","cafe"],
		"shop":["coffee"]
	}
	'''
	if not isinstance(tags, dict):
		return False
	for key in tags:
		if key in target_tags.keys():
			if ((tags[key] in target_tags[key])):
				return True
	return False

def to_geojson(self, heatmap):
	'''
	Helper function that wraps pandas.DataFrame.to_json

	Parameters
	----------
	heatmap: geopandas.GeoDataFrame
		Table with points and properties. 
		If geometries are polygons, they are replaced by their centroid.

	Returns
	-------
	json_heatmap: dict
		Heatmap in geojson format. 
	'''
	heatmap = gpd.GeoDataFrame(heatmap.drop('geometry',1),geometry=heatmap['geometry'])
	if any(heatmap.geometry.type!='Point'):
		heatmap.geometry = heatmap.geometry.centroid

	out = json.loads(heatmap.to_json())
	out['features'] = [{k:f[k] for k in ['geometry','properties']} for f in out['features']]
	return out
