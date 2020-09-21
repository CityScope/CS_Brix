# Classes

## Handler class


### class brix.Handler(table_name, GEOGRIDDATA_varname='GEOGRIDDATA', GEOGRID_varname='GEOGRID', quietly=True, host_mode='remote', reference=None)
Class to handle the connection for indicators built based on data from the GEOGRID. To use, instantiate the class and use the `add_indicator()` method to pass it a set of `Indicator` objects.


* **Parameters**

    
    * **table_name** (*str*) – Table name to lisen to.
    [https://cityio.media.mit.edu/api/table/table_name](https://cityio.media.mit.edu/api/table/table_name)


    * **GEOGRIDDATA_varname** (str, defaults to GEOGRIDDATA) – Name of geogrid-data variable in the table API.
    The object located at:
    [https://cityio.media.mit.edu/api/table/table_name/GEOGRIDDATA_varname](https://cityio.media.mit.edu/api/table/table_name/GEOGRIDDATA_varname)
    will be used as input for the return_indicator function in each indicator class.


    * **GEOGRID_varname** (str, defaults to GEOGRID) – Name of variable with geometries.


    * **quietly** (boolean, defaults to True) – If True, it will show the status of every API call.


    * **reference** (*dict**, **optional*) – Dictionary for reference values for each indicator.



#### add_indicator(I, test=True)
Adds indicator to handler object.


* **Parameters**

    
    * **I** (`brix.Indicator`) – Indicator object to handle. If indicator has name, this will use as identifier. If indicator has no name, it will generate an identifier.


    * **test** (boolean, defaults to True) – If True it will ensure the indicator runs before adding it to the `brix.Handler`.



#### add_indicators(indicator_list, test=True)
Same as `brix.Handler.add_indicator()` but it takes in a list of `brix.Indicator` objects.


* **Parameters**

    **indicator_list** (*list*) – List of `brix.Indicator` objects.



#### check_table(return_value=False)
Prints the front end url for the table.


* **Parameters**

    **return_value** (boolean, defaults to False) – If True it will print and return the front end url.



* **Returns**

    **front_end_url** – Onlye if return_value=True.



* **Return type**

    str



#### clear_table()
Clears all indicators from the table.


#### get_geogrid_data(include_geometries=False, with_properties=False, as_df=False)
Returns the geogrid data from:
[http://cityio.media.mit.edu/api/table/table_name/GEOGRIDDATA](http://cityio.media.mit.edu/api/table/table_name/GEOGRIDDATA)


* **Parameters**

    
    * **include_geometries** (boolean, defaults to False) – If True it will also add the geometry information for each grid unit.


    * **as_df** (boolean, defaults to False) – If True it will return data as a pandas.DataFrame.



* **Returns**

    **geogrid_data** – Data taken directly from the table to be used as input for `brix.Indicator.return_indicator`.



* **Return type**

    dict



#### get_geogrid_props()
Gets the GEOGRID properties defined for the table. These properties are not dynamic and include things such as the NAICS and LBCS composition of each lego type.


* **Returns**

    **geogrid_props** – Table GEOGRID properties.



* **Return type**

    dict



#### get_grid_hash()
Retreives the GEOGRID hash from:
[http://cityio.media.mit.edu/api/table/table_name/meta/hashes](http://cityio.media.mit.edu/api/table/table_name/meta/hashes)


#### get_indicator_values(include_composite=False)
Returns the current values of numeric indicators. Used for developing a composite indicator.


* **Parameters**

    **include_composite** (boolean, defaults to False) – If True it will also include the composite indicators, using the `brix.Indicator` is_composite parameter.



* **Returns**

    **indicator_values** – Dictionary with values for each indicator formatted as: `{indicator_name: indicator_value, ...}`



* **Return type**

    dict



#### get_table_properties()
Gets table properties. This info can also be accessed through `brix.Handler.get_geogrid_props()`.


#### indicator(name)
Returns the `brix.Indicator` with the given name.


* **Parameters**

    **name** (*str*) – Name of the indicator. See `brix.Handler.list_indicators()`.



* **Returns**

    **selected_indicator** – Selected indicator object.



* **Return type**

    `brix.Indicator`



#### list_indicators()
Returns list of all indicator names.


* **Returns**

    **indicators_names** – List of indicator names.



* **Return type**

    list



#### listen(showFront=True, append=False)
Listen for changes in the table’s geogrid and update all indicators accordingly.
You can use the update_package method to see the object that will be posted to the table.
This method starts with an update before listening.


* **Parameters**

    
    * **showFront** (boolean, defaults to True) – If True it will open the front-end URL in a webbrowser at start.


    * **append** (boolean, defaults to False) – If True it will append the new indicators to whatever is already there.



#### perform_update(grid_hash_id=None, append=True)
Performs single table update.


* **Parameters**

    
    * **grid_hash_id** (*str**, **optional*) – Current grid hash id. If not provided, it will retrieve it.


    * **append** (boolean, defaults to True) – If True, it will append the new indicators to whatever is already there.



#### return_indicator(indicator_name)
Returns the value returned by `brix.Indicator.return_indicator()` function of the selected indicator.


* **Parameters**

    **indicator_name** (*str*) – Name or identifier of the indicator. See `brix.Handler.list_indicators()`



* **Returns**

    **indicator_value** – Result of `brix.Indicator.return_indicator()` function for the selected indicator.



* **Return type**

    dict or float



#### rollback()
`brix.Handler` keeps track of the previous value of the indicators and access values.This function rollsback the current values to whatever the locally stored values are.
See also `brix.Handler.previous_indicators()` and `brix.Handler.previous_access()`.


#### see_current(indicator_type='numeric')
Returns the current values of the indicators posted for the table.


* **Parameters**

    **indicator_type** (str, defaults to numeric) – Type of the indicator. Choose either numeric, access, or heatmap (access and heatmap refer to the same type).



* **Returns**

    **current_status** – Current value of selected indicators.



* **Return type**

    dict



#### test_indicators()
Dry run over all indicators.


#### update_package(geogrid_data=None, append=False)
Returns the package that will be posted in CityIO.


* **Parameters**

    
    * **geogrid_data** (*dict**, **optional*) – Result of `brix.Handler.get_geogrid_data()`. If not provided, it will be retrieved.


    * **append** (boolean, defaults to False) – If True, it will append the new indicators to whatever is already there.



* **Returns**

    **new_values** – Note that all heatmat indicators have been grouped into just one value.



* **Return type**

    list


## Indicator class


### class brix.Indicator(\*args, \*\*kwargs)
Parent class to build indicators from. To use, you need to define a subclass than inherets properties from this class. Doing so, ensures your indicator inherets the necessary methods and properties to connect with a CityScipe table.


#### get_geogrid_data(as_df=False, include_geometries=None, with_properties=None)
Returns the geogrid data from the linked table. Function mainly used for development. See `brix.Indicator.link_table()`. It returns the exact object that will be passed to return_indicator


* **Parameters**

    **as_df** (boolean, defaults to False) – If True it will return data as a pandas.DataFrame.



* **Returns**

    **geogrid_data** – Data that will be passed to the `brix.Indicator.return_indicator()` function by the `brix.Handler` when deployed.



* **Return type**

    str or pandas.DataFrame



#### get_table_properties()
Gets table properties from the linked table. See `brix.Indicator.link_table()` and `brix.Handler.get_table_properties()`.


#### link_table(table_name)
Creates a `brix.Handler` and links the table to the indicator. This function should be used only for developing the indicator.


* **Parameters**

    **table_name** (str or `brix.Handler`) – Name of the table or Handler object.



#### load_module()
User defined function. Used to load any data necessary for the indicator to run. In principle, you could do everything using `brix.Indicator.setup()` but we encourage to separte data loading and module definition into two functions.


#### return_baseline(geogrid_data)
User defined function. Used to return a baseline value.
[This function might get deprecated]


#### return_indicator(geogrid_data)
User defined function. This function defines the value of the indicator as a function of the table state passed as geogrid_data. Function must return either a dictionary, a list, or a number. When returning a dict follow the format: `{'name': 'Indicator_NAME', 'value': 1.00}`.


* **Parameters**

    **geogrid_data** (*dict*) – Current state of the table. See `brix.Indicator.get_geogrid_data()` and `brix.Handler.get_geogrid_data()`. The content of this object will depend on the needs of the indicator. In particular, the values of `brix.Indicator.requires_geometry` and `brix.Indicator.requires_geogrid_props`.



* **Returns**

    **indicator_value** – Value of indicator or list of values. When returning a dict, please use the format `{'name': 'Indicator Name', 'value': indicator_value}`. When returning a list, please return a list of dictionaries in the same format.



* **Return type**

    list, dict, or float



#### setup()
User defined function. Used to set up the main attributed of the custom indicator. Acts similar to an __init__ method.

## Indicator sub-classes


### class brix.CompositeIndicator(\*args, \*\*kwargs)
Subclass used to define composite indicators. Composite indicators are functions of already defined indicators. By defining `brix.Indicator.setup()` and `brix.Indicator.return_indicator()`, this class allows you to define a composite indicator by just passing an aggregation function.


#### get_geogrid_data(as_df=False, include_geometries=None, with_properties=None)
Returns the geogrid data from the linked table. Function mainly used for development. See `brix.Indicator.link_table()`. It returns the exact object that will be passed to return_indicator


* **Parameters**

    **as_df** (boolean, defaults to False) – If True it will return data as a pandas.DataFrame.



* **Returns**

    **geogrid_data** – Data that will be passed to the `brix.Indicator.return_indicator()` function by the `brix.Handler` when deployed.



* **Return type**

    str or pandas.DataFrame



#### get_table_properties()
Gets table properties from the linked table. See `brix.Indicator.link_table()` and `brix.Handler.get_table_properties()`.


#### link_table(table_name)
Creates a `brix.Handler` and links the table to the indicator. This function should be used only for developing the indicator.


* **Parameters**

    **table_name** (str or `brix.Handler`) – Name of the table or Handler object.



#### load_module()
User defined function. Used to load any data necessary for the indicator to run. In principle, you could do everything using `brix.Indicator.setup()` but we encourage to separte data loading and module definition into two functions.


#### return_baseline(geogrid_data)
User defined function. Used to return a baseline value.
[This function might get deprecated]


#### return_indicator(indicator_values)
Applies `brix.CompositeIndicator.compose_function` to the indicator values to return the composite indicator.


* **Parameters**

    **indicator_values** (*dict*) – Dictionary with indicator values. See `brix.Handler.get_indicator_values()`.



* **Returns**

    **indicator_values** – List of one indicator.



* **Return type**

    list



#### setup(compose_function, selected_indicators=[], \*args, \*\*kwargs)
Indicator setup. This function is called upon __init__ so user does not need to call it independently.


* **Parameters**

    
    * **compose_function** (*function*) – Function to aggregate values of selected indicators. The function should be build to accept a dictionary with indicator values. See `brix.Handler.get_indicator_values()`.


    * **selected_indicators** (*list**, **optional*) – List of indicators to use to aggregate.
