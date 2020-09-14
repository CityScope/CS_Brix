# Brix

A python library for CityScope modules which handles communication with City I/O

## Introduction

What is this library for? If you have never heard of a CityScope before, you might want to stop reading and learn about them [here](https://cityscope.media.mit.edu/). CityScope is an awesome way to interact, explore, and co-create urban interventions in a way that can be accessed by multiple people with different background. If you know what they are, please keep reading.

What is a CityScope table? a 'table' is our way of describing a CityScope project. Why table then? Since historically, most CityScope instances were composed of a mesh between a physical table-top 3D model of a city, augmented with projections, software, and other interface hardware. So a table => project.

What is an indicator? An indicator is the result of running a module for CityScope. Indicators work by listening for updated from the CityScope table they are linked to, calculating some values by using a model, some function of the data, or a simulation, and then post the result of the calculations to CityIO to be displayed in the table.

What are the types of indicators you can build? Indicators can be anything that could be displayed on a CityScope table, including the supporting screens associated to it. For the purpose of this library, we distinguish three types of indicator: numeric, heatmap, simulation.

-   Numeric: Numeric indicators are just a number or set of numbers. They are usually displayed in a chart (bar chart, radar chart, etc) next to the table. The most common numeric indicator are the numbers that go in the radar plot, which display information about density, diversity, and proximity.

-   Heatmap: These indicators are geodata. They are made up of geometries (points, lines, or polygons) and properties associated to them. These indicators are displayed as layers directly on the CityScope table.
-   Simulation: These type of indicators are also displayed on the table but they are the result of an agent based simulation and are therefore displayed as a dynamic layer. They change over time like a short movie. These are not yet supported by this library.

## Tutorial

### Basics of building a CityScope indicator

Let's get to it. First, what table are you building for? If you don't have a specific table, that is totally okay and you can create one [here](https://cityscope.media.mit.edu/CS_cityscopeJS/). Note: by the time you read this, CityScope might pose some limitations on new projects ('tables'). Please follow instructions in the link above. 
For this tutorial, we crated one called `dungeonmaster`.

An indicator will basically take in data, and produce a result. Each new indicator is built as an subclass of the `Indicator` class provided in this library. Make sure you define three functions: `setup`, `load_module`, and `return_indicator`. Here's a barebones example of an indicator:

```
from brix import Indicator
class MyIndicator(Indicator):
	'''
	Write a description for your indicator here.
	'''
	def setup(self):
		'''
		Think of this as your __init__.
		Here you will define the properties of your indicator.
		Although there are no required properties, be nice and give your indicator a name.
		'''
		self.name = 'Alfonso'

	def load_module(self):
		'''
		This function is not strictly necessary, but we recommend that you define it if you want to load something from memory. It will make your code more readable.
		'''
		pass

	def return_indicator(self, geogrid_data):
		'''
		This is the main course of your indicator.
		This function takes in `geogrid_data` and returns the value of your indicator.
		The library is flexible enough to handle indicators that return a number or a dictionary.
		'''
		return 1
```

### Let's talk input/data

What is `geogrid_data`?
Every time we create a CityScope table, we define a regularly spaced grid which is overlaid on the city district we're modelling. These grid cells are the basic unit of analysis for the CityScope modules. Every grid cell has properties such as the 'Type' which represents the land use and 'Height' which represents the number of floors. These data are dynamic and are updated each time a user interacts with the CityScope table, experimenting with the spatial organisation of land uses and infrastructure. These dynamic data are stored the variable `geogrid_data`. This is a list of ojects: one for each grid cell in the CityScope table. The contents of each object really depends on the specific table you are building for and on the properties assigned to your indicator. There are two options that will control what `geogrid_data` contains which are: `Indicator.requires_geometry` and `Indicator.requires_geogrid_props`. These two properties are set to `False` by default, but you can change them inside the `setup` function depending on the needs of your indicator.

Go ahead, take a look at how this object looks like by instantiating your class and linking it to a table:

```
I = MyIndicator()
I.link_table('dungeonmaster')
I.get_geogrid_data()
```

Please note that the `link_table` should only be used when developing the indicator. For deployment, we'll use the `Handler` class that is more efficient. You can also skip the `link_table` step by defining the `Indicator.table_name='dungeonmaster'` property in your `setup` function. You will also notice that as you change the `Indicator.requires_geometry` and `Indicator.requires_geogrid_props` parameters in `setup`, the output of `get_geogrid_data` will change.

If you are testing and are curious how `geogrid_data` would look like if you set `requires_geometry=True`, you can pass the argument to `get_geogrid_data`:

```
I.get_geogrid_data(include_geometries=True)
```

### Build and test your indicator (output)

This library ensures that you can focus on what you do best: writing a kick ass `return_indicator` function that will make everyone's urban planning life better.

To test your function while debugging it, you can use the object returned by `get_geogrid_data`:

```
geogrid_data = I.get_geogrid_data()
I.return_indicator(geogrid_data)
```

The property `Indicator.indicator_type` will toggle between a Heatmap indicator or a numeric indicator (`numeric` for nueric and `heatmap` for heatmap).

For numeric indicators, there are multiple ways in which the front end can display them (e.g. bar chart, radar plot, etc.). This is controlled by the `viz_type` property of the class. The default value is set to `Indicator.viz_type=radar` which means that unless it is specified otherwise, all numeric indicators will be added to the radar plot. When building an indicator that returns a single number you can just change the value of this parameter in the `setup()`. When building an indicator that returns multiple numbers it will just assume every number should be displayed in the same front end visualization. If you want to have more fine control of where each indicator is displayed, we recommend building your `return_indicator` function such that it returns a dictionary with the following structure:

```
{
	'name': 'Social Wellbeing',
	'value': random.random(),
	'viz_type': 'bar'
}
```

The `viz_type` defined in the return object of `return_indicator` will overwrite any default property defined in `setup`. Remember that your `return_indicator` function can also return a list of indicators. In the following example of a return value for the `return_indicator` function, the indicator returns two numbers that should be displayed in the radar plot, and one to be displayed as a bar chart.

```
[
	{'name': 'Social Wellbeing', 'value': 0.3, 'viz_type': 'radar'},
	{'name': 'Environmental Impact', 'value': 0.1, 'viz_type': 'radar'},
	{'name': 'Mobility Impact', 'value': 0.5, 'viz_type': 'bar'}
]
```

### Deploy your indicator

Finally, once you have build a series of indicators, the right way to deploy them is to use the `Handler` class. A `Handler` object should be the go-to connection to the table and will handle all possible exceptions. The two most important methods are `add_indicators` which takes a list of `Indicator` objects and connects them to the table, and `listen` that is a method that runs continuously waiting for updates in the CityScope table. The example below assumes you have already defined indicators named Density, Diversity and Proximity in a file named myindicators.py.

```
from brix import Handler
from myindicators import Density, Diversity, Proximity

dens = Density()
divs = Diversity()
prox = Proximity()

H = Handler('dungeonmaster', quietly=False)
H.add_indicators([
	dens,
	divs,
	prox
])
H.listen()
```

To see the indicators in the handler you can use `H.list_indicators()` to list the indicator names, and use `H.return_indicator(<indicator_name>)` to see the value of the indicator. Finally, the function `H.update_package()` will return the data that will be posted on CityIO.

## Examples

### Numeric indicator: diversity

Indicators are built as subclasses of the **Indicator** class, with three functions that need to be defined: _setup_, _load_module_, and _return_indicator_. The function _setup_ acts like an _**init**_ and can take any argument and is run when the object is instantiated. The function _load_module_ is also run when the indicator in initialized, but it cannot take any arguments. Any inputs needed for _load_module_ should be defined as properties in _setup_. The function _return_indicator_ is the only required one and should take in a 'geogrid*data' object and return the value of the indicator either as a number, a dictionary, or a list of dictionaries/numbers. Sometimes, the indicator requires geographic information from the table to calculate it. To get geographic information from the table, set the property \_requires_geometry* to True (see Noise heatmap as an example).

The following example implements a diversity-of-land-use indicator:

```
from brix import Indicator
from brix import Handler

from numpy import log
from collections import Counter

class Diversity(Indicator):

	def setup(self):
		self.name = 'Entropy'

	def load_module(self):
		pass

	def return_indicator(self, geogrid_data):
		uses = [cell['land_use'] for cell in geogrid_data]
		uses = [use for use in uses if use != 'None']

		frequencies = Counter(uses)
		total = sum(frequencies.values(), 0.0)
		entropy = 0
		for key in frequencies:
			p = frequencies[key]/total
			entropy += -p*log(p)

		return entropy

div = Diversity()

H = Handler('dungeonmaster', quietly=False)
H.add_indicator(div)
H.listen()
```

### Composite indicator: average

In some settings, it might be useful to aggregate different indicators to get a average feel of what the neighborhood looks like. For this use case, `brix` provides a simplified `CompositeIndicator` class that only needs an aggregation function.

Let's create an indicator that averages Innovation Potential, Mobility Inmpact, and Economic Impact. We use the `CompositeIndicator` class for this. This class takes an aggregate function as input. This function should take the result of `Handler.get_indicator_values()` as input and returns a number. If you want to have more control over what the `CompositeIndicator` does you can always extend the class.

Here is the simplest example that averages the values of three indicators:

```
from brix import Handler, CompositeIndicator
from brix.examples import RandomIndicator

def innovation_average(indicator_values):
    avg = (indicator_values['Innovation Potential']+indicator_values['Mobility Impact']+indicator_values['Economic Impact'])/3
    return avg

H = Handler('dungeonmaster')
R = RandomIndicator()
avg_I = CompositeIndicator(innovation_average,name='Composite')
H.add_indicators([R,avg_I])
```

In some cases, the aggregation function is too simple to write it again. In the example before, you can also pass it a pre-existing function, such as `np.mean`, making sure that you select the indicators that will be passed as input, by their name.

```
from brix import Handler, CompositeIndicator
from brix.examples import RandomIndicator
import numpy as np

H = Handler('dungeonmaster')
R = RandomIndicator()
avg_I = CompositeIndicator(np.mean,selected_indicators=['Innovation Potential','Mobility Impact','Economic Impact'],name='Composite')
H.add_indicators([R,avg_I])
```

### Heatmap indicator

The same class can be used to define a heatmap or accessiblity indicator, as opposed to a numeric indicator.
First, set the class property _indicator_type_ equal to 'heatmap' or to 'access'. This will flag the indicator as a heatmap and will tell the Handler class what to do with it.
Second, make sure that the _return_indicator_ function returns a list of features or a geojson.
The example below shows an indicator that returns noise for every point in the center of a grid cell. Because this indicator needs the coordinates of table to return the geojson, it sets the property _requires_geometry_ to True.

```
from brix import Indicator
class Noise(Indicator):
    '''
    Example of Noise heatmap indicator for points centered in each grid cell.

    Note that this class requires the geometry of the table as input, which is why it sets:
    requires_geometry = True
    in the setup.

    '''
    def setup(self):
        self.indicator_type = 'heatmap'
        self.requires_geometry = True

    def load_module(self):
        pass

    def return_indicator(self, geogrid_data):
        features = []
        for cell in geogrid_data:
            feature = {}
            lat,lon = zip(*cell['geometry']['coordinates'][0])
            lat,lon = mean(lat),mean(lon)
            feature['geometry'] = {'coordinates': [lat,lon],'type': 'Point'}
            feature['properties'] = {self.name:random()}
            features.append(feature)
        out = {'type':'FeatureCollection','features':features}
        return out
```

## Step by step examples

### Diversity of land-use indicator - step by step

As an example, we'll build a diversity of land use indicator for the test table. The process is the same for any table, provided that it has a GEOGRID variable. Indicators are built as subclasses of the **Indicator** class, with three functions that need to be defined: _setup_, _load_module_, and _return_indicator_. The function _setup_ acts like an _**init**_ and can take any argument and is run when the object is instantiated. The function _load_module_ is also run when the indicator in initialized, but it cannot take any arguments. Any inputs needed for _load_module_ should be defined as properties in _setup_. The function _return_indicator_ is the only required one and should take in a 'geogrid_data' object and return the value of the indicator either as a number, a dictionary, or a list of dictionaries/numbers.

To start developing the diversity indicator, you can use the Handler class to get the geogrid*data that is an input of the \_return_indicator* function.

```
from brix import Handler
H = Handler('dungeonmaster')
geogrid_data = H.geogrid_data()
```

The returned _geogrid_data_ object depends on the table, but for dungeonmaster it looks like this:

```
[
	{
		'color': [0, 0, 0, 0],
		'height': 0.1,
		'id': 0,
		'interactive': True,
		'land_use': 'None',
		'name': 'empty',
		'tui_id': None
	},
	{
		'color': [247, 94, 133, 180],
		'height': [0, 80],
		'id': 1,
		'interactive': True,
		'land_use': 'PD',
		'name': 'Office Tower',
		'old_color': [133, 94, 247, 180],
		'old_height': [0, 10],
		'tui_id': None
	},
	{
		'color': [0, 0, 0, 0],
		'height': 0.1,
		'id': 2,
		'interactive': True,
		'land_use': 'None',
		'name': 'empty',
		'tui_id': None
	},
	...
]
```

We build the diversity indicator by delecting the 'land_use' variable in each cell and calculating the Shannon Entropy for this:

```
from numpy import log
from collections import Counter
uses = [cell['land_use'] for cell in geogrid_data]
uses = [use for use in uses if use != 'None']

frequencies = Counter(uses)

total = sum(frequencies.values(), 0.0)
entropy = 0
for key in frequencies:
	p = frequencies[key]/total
	entropy += -p*log(p)
```

Now, we wrap this calculation in the _return_indicator_ in a Diversity class that inherits the properties from the Indicator module:

```
from brix import Indicator
from numpy import log
from collections import Counter

class Diversity(Indicator):

	def setup(self):
		self.name = 'Entropy'

	def load_module(self):
		pass

	def return_indicator(self, geogrid_data):
		uses = [cell['land_use'] for cell in geogrid_data]
		uses = [use for use in uses if use != 'None']

		frequencies = Counter(uses)

		total = sum(frequencies.values(), 0.0)
		entropy = 0
		for key in frequencies:
			p = frequencies[key]/total
			entropy += -p*log(p)

		return entropy
```

Because this indicator is very simple, it does not need any parameters or data to calculate the value, which is why the _load_module_ function is empty. The _setup_ function defines the properties of the module, which in this case is just the name.

Finally, we run the indicator by instantiating the new class and passing it to a Handler object:

```
from brix import Handler

div = Diversity()

H = Handler('dungeonmaster', quietly=False)
H.add_indicator(div)
H.listen()
```

### Composite indicator -- step by step tutorial

Let's create an indicator that averages Innovation Potential, Mobility Inmpact, and Economic Impact.
First, we load the RandomIndicator and pass it to a Handler.

```
from brix import Handler, CompositeIndicator
from brix.examples import RandomIndicator

H = Handler('dungeonmaster')
R = RandomIndicator()
H.add_indicator(R)
```

To develop the aggregate function, we use the `get_indicator_values()` function from the handler class. We need to make sure our aggregate function works with that the Handler is returning:

```
indicator_values = H.get_indicator_values()
```

In this case, the `indicator_values` is a dictionary with the following elements:

```
{
	'Social Wellbeing': 0.9302328967423512,
	'Environmental Impact': 0.8229183561962108,
	'Mobility Impact': 0.3880460148817071,
	'Economic Impact': 0.13782084927373295,
	'Innovation Potential': 0.8913823890081203
}
```

We do not need to use all of the values returned by the Handler for our indicator. \

Next, we write our simple average function that takes `indicator_values` as input and returns a value, and pass it as an argument to the `CompositeIndicator` class constructor.

```
def innovation_average(indicator_values):
    avg = (indicator_values['Innovation Potential']+indicator_values['Mobility Impact']+indicator_values['Economic Impact'])/3
    return avg

avg_I = CompositeIndicator(innovation_average,name='Composite')
```

To make sure it is running, we can test it as usual:

```
avg_I.return_indicator(indicator_values)
```

We finally add it to the Handler:

```
H.add_indicator(avg_I)
```

### Heatmap indicator -- step by step tutorial

This section will show you step by step how to build a proximity to parks indicator.

Let's start by setting up a simple subclass of the Indicator class, give it a name, and set it as a `heatmap` indicator:
```
from brix import Indicator
class ProximityIndicator(Indicator):
	def setup(self):
		self.name = 'Parks'
		self.indicator_type = 'heatmap'

	def return_indicator(self, geogrid_data):
		pass
```

Next, we link it to the table. This step is only for building the indicator as we use a `Handler` object when deploying it. 

```
P = ProximityIndicator()
P.link_table('dungeonmaster')
P.get_geogrid_data()
```
When running `get_geogrid_data` we see that every cell has a `name` property and some cells are classified as `Park`. You'll also notice that by default, when building a `heatmap` indicator, `geogrid_data` returns the geometries. You can change this behavior by setting `self.requires_geometry=False` in your `setup`.

Next, we define the `return_indicator` function. For debugging and testing you can define this function as stand alone function before adding it as a method to the ProximityIndicator. Some useful functions for debugging are `P.get_geogrid_data()` and `P.get_table_properties()` that will list general properties of the linked table. 

In this example, the proximity indicator is defined as one over the distance to the closest park. When the cell is a park, we define the proximity as 1/(half size of each cell) to avoid dividing by zero.

```
import numpy as np
from geopy.distance import distance as geodistance # Function for distance between coordinates

def return_indicator(self,geogrid_data):
	parks = [cell for cell in geogrid_data if cell['name']=='Park'] # Find all parks
	parks_locations = [np.mean(cell['geometry']['coordinates'][0],0) for cell in parks] # Filter out the center of all park locations (locations are lon,lat format)

	features = []
	for cell in geogrid_data: # Calculate a value for the indicator for each cell
		cell_coords = np.mean(cell['geometry']['coordinates'][0],0) # Calculate center of cell (locations are lon,lat format)
		if cell['name']=='Park': # If cell is park, set distance to zero
			park_distance = 25 # This is based on half the cell size (see P.get_table_properties()) 
		else:
			distances = [geodistance(cell_coords[::-1],park_loc[::-1]).m for park_loc in parks_locations] # Distance between cell and each park. Notice that we reverse the coordinates for geodistance.
			park_distance = min(distances) # get distance to closest park

		proximity = 1/park_distance
		scaled_proximity = (proximity-0.002)/(0.03-0.002) # this ensures the indicator is between zero and one

		# Generate feature with points (lon,lat format) and properties.
		feature = {} 
		feature['geometry'] = {'coordinates': list(cell_coords),'type': 'Point'} # cell_coords should be a list
		feature['properties'] = {self.name: scaled_proximity} # Use the indicator name to tag the value

		features.append(feature) # add to features list for export

	out = {'type':'FeatureCollection','features':features}
	return out
```

You can test your function by running: `return_indicator(P,geogrid_data)`.

Finally, let's put it all together:
```
from brix import Indicator
import numpy as np
from geopy.distance import distance as geodistance

class ProximityIndicator(Indicator):
	def setup(self):
		self.name = 'Parks'
		self.indicator_type = 'heatmap'

	def return_indicator(self,geogrid_data):
		parks = [cell for cell in geogrid_data if cell['name']=='Park']
		parks_locations = [np.mean(cell['geometry']['coordinates'][0],0) for cell in parks]

		features = []
		for cell in geogrid_data: 
			cell_coords = list(np.mean(cell['geometry']['coordinates'][0],0) )
			if cell['name']=='Park': 
				park_distance = 45 
			else:
				distances = [geodistance(cell_coords[::-1],park_loc[::-1]).m for park_loc in parks_locations]
				park_distance = min(distances) 

			proximity = 1/park_distance
			scaled_proximity = (proximity-0.002)/(0.03-0.002) 

			feature = {} 
			feature['geometry'] = {'coordinates': cell_coords,'type': 'Point'}
			feature['properties'] = {self.name: scaled_proximity} 

			features.append(feature)

		out = {'type':'FeatureCollection','features':features}
		return out
```

And to deploy it:
```
from brix import Handler
H = Handler('dungeonmaster')
P = ProximityIndicator()
H.add_indicator(P)
H.listen()
```

