# Helper functions live here

def is_number(s):
	'''
	Returns True if input can be turned into a number, else Fals
	'''
	try:
		float(s)
		return True
	except:
		return False

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