# CS_Brix
A python library for CityScope modules which handles communication with City I/O

## Custom GEOGRID indicator (tldr)

Indicators are built as subclasses of the **Indicator** class, with three functions that need to be defined: *setup*, *load_module*, and *return_indicator*. The function *setup* acts like an *__init__* and can take any argument and is run when the object is instantiated. The function *load_module* is also run when the indicator in initialized, but it cannot take any arguments. Any inputs needed for *load_module* should be defined as properties in *setup*. The function *return_indicator* is the only required one and should take in a 'geogrid_data' object and return the value of the indicator either as a number, a dictionary, or a list of dictionaries/numbers. Sometimes, the indicator requires geographic information from the table to calculate it. To get geographic information from the table, set the property *requires_geometry* to True (see Noise heatmap as an example). 

The following example implements a diversity-of-land-use indicator:
```
from toolbox import Indicator
from toolbox import Handler

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

H = Handler('corktown', quietly=False)
H.add_indicator(div)
H.listen()
```


## Custom Composite indicator (tldr)

Let's create an indicator that averages Innovation Potential, Mobility Inmpact, and Economic Impact. We use the `CompositeIndicator` class for this. This class takes an aggregate function as input. This function takes in the result of `Handler.get_indicator_values()` as input and returns a number. If you want to have more control over what the `CompositeIndicator` does you can always extend the class.

```
from toolbox import Handler, CompositeIndicator
from examples import RandomIndicator

def innovation_average(indicator_values):
    avg = (indicator_values['Innovation Potential']+indicator_values['Mobility Impact']+indicator_values['Economic Impact'])/3
    return avg

H = Handler('corktown')
R = RandomIndicator()
avg_I = CompositeIndicator(innovation_average,name='Composite')
H.add_indicators([R,avg_I])
```

You can also pass it a pre-existing function, such as `np.mean`. 
```
from toolbox import Handler, CompositeIndicator
from examples import RandomIndicator
import numpy as np

H = Handler('corktown')
R = RandomIndicator()
avg_I = CompositeIndicator(np.mean,selected_indicators=['Innovation Potential','Mobility Impact','Economic Impact'],name='Composite')
H.add_indicators([R,avg_I])
```


## Custom Composite indicator

Let's create an indicator that averages Innovation Potential, Mobility Inmpact, and Economic Impact.
First, we load the RandomIndicator and pass it to a Handler.

```
from toolbox import Handler, CompositeIndicator
from examples import RandomIndicator

H = Handler('corktown')
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


## Custom accessibility indicator

The same class can be used to define a heatmap or accessiblity indicator, as opposed to a numeric indicator.
First, set the class property *indicator_type* equal to 'heatmap' or to 'access'. This will flag the indicator as a heatmap and will tell the Handler class what to do with it.
Second, make sure that the *return_indicator* function returns a list of features or a geojson. 
The example below shows an indicator that returns noise for every point in the center of a grid cell. Because this indicator needs the coordinates of table to return the geojson, it sets the property *requires_geometry* to True.

```
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

## GEOGRID indicator tutorial - Diversity of land-use indicator

As an example, we'll build a diversity of land use indicator for the corktown table. The process is the same for any table, provided that it has a GEOGRID variable. Indicators are built as subclasses of the **Indicator** class, with three functions that need to be defined: *setup*, *load_module*, and *return_indicator*. The function *setup* acts like an *__init__* and can take any argument and is run when the object is instantiated. The function *load_module* is also run when the indicator in initialized, but it cannot take any arguments. Any inputs needed for *load_module* should be defined as properties in *setup*. The function *return_indicator* is the only required one and should take in a 'geogrid_data' object and return the value of the indicator either as a number, a dictionary, or a list of dictionaries/numbers. 

To start developing the diversity indicator, you can use the Handler class to get the geogrid_data that is an input of the *return_indicator* function.
```
from toolbox import Handler
H = Handler('corktown')
geogrid_data = H.geogrid_data()
```

The returned *geogrid_data* object depends on the table, but for corktown it looks like this:
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

Now, we wrap this calculation in the *return_indicator* in a Diversity class that inherits the properties from the Indicator module: 
```
from toolbox import Indicator
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

Because this indicator is very simple, it does not need any parameters or data to calculate the value, which is why the *load_module* function is empty. The *setup* function defines the properties of the module, which in this case is just the name. 

Finally, we run the indicator by instantiating the new class and passing it to a Handler object:
```
from toolbox import Handler

div = Diversity()

H = Handler('corktown', quietly=False)
H.add_indicator(div)
H.listen()
```
