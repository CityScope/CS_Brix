# Functions

## Wrapper functions

These functions work as shortcuts to build indicators.


### brix.make_numeric_indicator(name, return_indicator, viz_type='bar', requires_geometry=False, requires_geogrid_props=False)
Function that constructs and indicator based on a user defined return_indicator function.


* **Parameters**

    
    * **name** (*str*) – Name of the indicator.


    * **return_indicator** (*func*) – Function that takes in geogrid_data and return the value of the indicator.


    * **viz_type** (*str**, **defaults to 'bar'*) – Visualization type in front end. Used for numeric indicators.


    * **requires_geometry** (boolean, defaults to False) – If True, the geogrid_data object will also come with geometries.


    * **requires_geogrid_props** (boolean, defaults to False) – If True, the geogrid_data object will include properties.



* **Returns**

    **I** – Numeric indicator that returns the value of the given function.



* **Return type**

    `brix.Indicator`


## OSM functions

These functions help you get data from Open Street Maps for your table.


### brix.get_OSM_geometries(H, tags={'building': True}, buffer_percent=0.25, use_stored=True, only_polygons=True)
Gets the buildings from OSM within the table’s geogrid.
This function requires osmnx package to be installed.
Simple usage: buildings = OSM_geometries(H).


* **Parameters**

    
    * **H** (`brix.Handler`) – Table Handler.


    * **tags** (*dict**, **defaults to building*) – Tags of geometries to get. See: osmnx.geometries_from_polygon


    * **buffer_percent** (*float**, **defaults to 0.25*) – Buffer to use around the table.
    Size of buffer in units of the grid diameter
    See `brix.get_buffer_size()`.


    * **use_stored** (*boolean**, **defaults to True*) – If True, the function will retrieve the results once and save them in the Handler under the `brix.Handler.OSM_data` attribute.
    If False, the function will retrieve the results every time it is called.


    * **only_polygons** (*boolean**, **defaults to True*) – If False, it will return all buildings, including those without their polygon shape (e..g some buildings just have a point).



* **Returns**

    **buildings** – Table with geometries from OSM.



* **Return type**

    geopandas.GeoDataFrame



### brix.get_OSM_nodes(H, expand_tags=False, amenity_tag_categories=None, use_stored=True, buffer_percent=0.25, quietly=True)
Returns the nodes from OSM.
This function can be used to obtain a list of amenities within the area defined by the table.
There is a default buffer added around the grid, but you can increase this by changing buffer_percent.


* **Parameters**

    
    * **H** (`brix.Handler`) – Table Handler.


    * **expand_tags** (*boolean**, **defaults to False.*) – If True, it will expand all the tags into a wide format with one column per tag.
    Columns will be named as: tag_{tag}


    * **amenity_tag_categories** (*dict** (**optional**)*) – Dictionary with categories of amenities.
    For example:

    > {

    >     “restaurants”: {

    >         “amenity”:[“restaurant”,”cafe”,”fast_food”,”pub”,”cafe”],
    >         “shop”:[“coffee”]

    >     },
    >     “nightlife”: {

    >     > ”amenity”:[“bar”,”pub”,”biergarten”,”nightclub”]

    >     }

    > }

    Will add two new columns: “category_restaurants” and “category_nightlife”



    * **use_stored** (*boolean**, **defaults to True*) – If True, the function will retrieve the results once and save them in the Handler under the `brix.Handler.OSM_data` attribute.
    If False, the function will retrieve the results every time it is called.


    * **buffer_percent** (*float**, **defaults to 0.25*) – Buffer to use around the table.
    Size of buffer in units of the grid diameter
    See get_buffer_size.


    * **quietly** (*boolean**, **defaults to False*) – If True, it will print the generated URL



* **Returns**

    **node_data_df** – Table with all the nodes within the bounds.



* **Return type**

    geopandas.GeoDataFrame
