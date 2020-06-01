# CS_Grik_Maker

This repo provides a class for creating spatial grids for CityScope projects.
- Create a spatial grid geojson based on an origin point, rotation and numbers of rows/columns
- Create an 'interactive region' by specfiying the interactive rows and columns (rectangular region) or overlaying a geojson (irregular region).
- Assign properties (eg. land use, effective num floors) to each grid cell by overlaying GIS data

This project is meant to be used as a utility for the [CityScope platform](https://github.com/CityScope)

## Basic Usage
### Create a grid object
```
top_left_lon =  -83.090119
top_left_lat = 42.336341

nrows = 92
ncols = 80

rotation = 23


cell_size = 25
crs_epsg = '26917'

grid = Grid(top_left_lon, top_left_lat, rotation,
            crs_epsg, cell_size, nrows, ncols)
```

### Specify a rectangular interactive region (for TUI)
```
tui_top_left_row_index=20
tui_top_left_col_index=10
tui_num_interactive_rows=20
tui_num_interactive_cols=20

grid.add_tui_interactive_cells(tui_top_left_row_index, tui_top_left_col_index,
                                  tui_num_interactive_rows, tui_num_interactive_cols)
```

### Specify an irregular interactive region for web-based interaction
```

interactive_region=json.load('interactive_region.geojson')
grid.set_web_interactive_region(interactive_region)
```
### Set properties of grid cells from GIS data
```
parcel_data=json.load(open('parcel_data.geojson'))
    
parcel_properties={'type': {'from':'CS_LU', 'default': 'None'}, 
                   'height': {'from':'effective_num_floors', 'default': 0},
                   'year': {'from':'year_built', 'default': 0}
                   }
grid.set_grid_properties_from_shapefile(parcel_data, parcel_properties)
```

### Create the geojson
```
grid_geo=grid.get_grid_geojson(add_properties={})
```

### Save geojson to file
```
json.dump(grid_geo, open('geogrid.geojson', 'w'))
```

