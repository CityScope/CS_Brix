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