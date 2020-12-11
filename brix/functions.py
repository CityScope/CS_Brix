# Other functions that use brix objects (e.g. function to get street network for table from OSM)

from .classes import Handler
from .classes import Indicator
from .classes import CompositeIndicator
from .classes import GEOGRIDDATA

def add_height(geogrid_data, levels):
  for cell in geogrid_data:
    cell['height'] += levels
  return geogrid_data