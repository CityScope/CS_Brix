# Other functions that use brix objects (e.g. function to get street network for table from OSM)

from .classes import Handler
from .classes import Indicator
from .classes import CompositeIndicator
from .classes import GEOGRIDDATA

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
