Tutorials
=========

This module also contains a set of other useful functions that integrate with :class:`brix.Handler` and :class:`brix.Indicator`. 

The functions :func:`brix.get_OSM_geometries` and :func:`brix.get_OSM_nodes` help you get data from Open Street Maps for your table. 

Auto-updates of GEOGRIDDATA
---------------------------

Brix also has the capability of automatically updating GEOGRIDDATA. For simple one-time updates, follow the documentation of :func:`brix.Handler.update_geogrid_data`. To use this feeature, you first need to define a function that takes a :class:`brix.GEOGRIDDATA` as an input. When used with :func:`brix.Handler.update_geogrid_data`, this function can take any number of keyword arguments. The following example raises the height of all cells by 3 units:

::

	def add_height(geogrid_data, levels=1):
		for cell in geogrid_data:
			cell['height'] += levels
		return geogrid_data

	H = Handler('dungeonmaster', quietly=False)
	H.update_geogrid_data(add_height,levels=3)

Brix also supports GEOGRIDDATA updates everytime there is a registered user interaction in the front end. To add a function to the update schedule, use :func:`brix.Handler.add_geogrid_data_update_function`. This has the limitation that your update funcion cannot take in any arguments other. If this limitation proves too restrictive, please submit an issue and we'll consider pushing an update. 

The following example updates the whole grid to `Light Industrial` use everytime there's a user interaction:

::

	def update_g(geogrid_data):
		for cell in geogrid_data:
			cell['name'] = 'Light Industrial'
		return geogrid_data

	H = Handler(table_name,quietly=False)
	H.add_geogrid_data_update_function(update_g)
	H.listen()

The updates triggered by :func:`brix.Handler.listen` follow the following order: 

1) get GEOGRIDDATA 
2) run all GEOGRIDDATA updates using the result of 1 as input
3) get the new GEOGRIDDATA
4) update all indicators using the GEOGRIDDATA object resulting from 3

Creating a table from python
----------------------------

`Brix` provides a class for creating spatial grids for CityScope projects: :class:`brix.Grid` a subclass of :class:`brix.Handler`.

For most use cases, you will create your table using the web-app editor found `here <https://cityscope.media.mit.edu/CS_cityscopeJS/#/editor>`_. For more complex projects, you might need to create your own table from an existing dataset. For example, you might want to select the grid area using a polygon defined in a shapefile. The tools we highlight here can be use for this purpose.

The first step is to instantiate the class by defining the location of your table and its name. The lat,lon provided to the :class:`brix.Grid` constructor correspond to the top left corner of the grid (North-West).

::

	from brix import Grid
	table_name = 'dungeonmaster'
	lat,lon = 42.361875, -71.105713
	G = Grid(table_name, lat, lon)

If the table already exists, you can either ignore this and you will be prompted if you want to rewrite it, or use :func:`brix.Handler.delete_table` to delete it before creating it. Alternatively, you can check if the table exists by using :func:`brix.Handler.is_table`. Please note that since :class:`brix.Grid` is a subclass of :class:`brix.Handler`, most functions available for a :class:`brix.Handler` object are also available for a :class:`brix.Grid` object.






Testing your module
-------------------

To automatically test your module, this library provides the :class:`brix.User` class that simulates the behavior of a user interacting with your grid. This user runs in its own new thread to free up your main thread so that you can keep wokring on your indicator.

The following example consists of a :class:`brix.Handler` that contains a diversity :class:`brix.Indicator` that reponds to the updates of the :class:`brix.User`:

::

	from brix import Handler
	from brix.examples import Diversity
	from brix.test_tools import User
	table_name = 'dungeonmaster'
	U = User(table_name)
	H = Handler(table_name,quietly=False)
	div = Diversity()
	H.add_indicator(div)
	U.start_user()
	H.listen()

