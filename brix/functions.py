# Other functions that use brix objects (e.g. function to get street network for table from OSM)

from .classes import Handler
from .classes import Indicator
from .classes import CompositeIndicator
from .classes import GEOGRIDDATA

import requests
import json

def update_geogrid_data(H, update_func, geogrid_data=None, **kwargs):
  '''
  High order function to update table geogrid data. Based on `update_package`
   and `perform_update` methods from `Handler` class.

  NOTE: From @crisjf "Eventually could be added as a method of the Handler"
  WARNING: From @RELNO: "Edits to the grid from a different source might not be
  reflected or break the FE, as it has multiple internal dependencies other than
  the grid itself."

  Parameters
  ----------
  H : brix.Handler
    brix.Handler instance (linked to an specific table)
  update_func : function
    function to update the geogriddadata (list of dicts)

  Example
  -------
  >>> def add_height(geogrid_data, levels):
          for cell in geogrid_data:
              cell['height'] += levels
          return geogrid_data
  >>> H = Handler('tablename', quietly=False)
  >>> update_landuse(H, add_height)
  '''
  grid_hash_id = H.get_grid_hash()
  if geogrid_data is None:
    geogrid_data = H._get_grid_data()

  if not H.quietly:
    print('Updating table with hash:', grid_hash_id)

  new_geogrid_data = update_func(geogrid_data, **kwargs)
  new_geogrid_data = GEOGRIDDATA(new_geogrid_data)
  new_geogrid_data.link_table(H)
  if not new_geogrid_data.check_type_validity():
    raise NameError('Type not found in table definition')

  if not new_geogrid_data.check_id_validity():
    raise NameError('IDs do not match')

  r = requests.post(H.cityIO_post_url+'/'+H.GEOGRIDDATA_varname, data=json.dumps(new_geogrid_data))

  if not H.quietly:
    print('Done with update')
