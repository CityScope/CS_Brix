#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 18:57:59 2019

@author: doorleyr
@contributors: crisjf, guadalupebabio
"""
from .classes import Handler
from .helpers import deg_to_rad, rad_to_deg, get_timezone_offset, hex_to_rgb
from .functions import normalize_table_name, check_table_name

import pyproj
import math
import numpy as np
import matplotlib.path as mplPath
import requests
import matplotlib.pyplot as plt
import copy
import json
import traceback
import matplotlib
from vincenty import vincenty
from warnings import warn
from shapely.geometry import shape

class Grid_maker(Handler):
    """
    Takes the properties of the grid and using the Haversine formula, 
    computes the location of the top-right corner. Then projects
    to spatial coordinates in order to find the locations of the rest of 
    the grid cells

    Parameters
    ----------
    table_name: str
        Name of table to create.
        It will overwrite it if it exists.
    top_left_lat: float
        Latitude of top left corner of grid
    top_left_lon: float
        Longitude of top left corner of grid
    cell_size: float, defaults to 100
        Lenght in meters of the side of each cell.
    nrows: int, defaults to 20
        Number of rows
    ncols: int, defaults to 20
        Number of columns
    rotation: int, defaults to 0
        Roation of the grid.
    crs_epsg: str
        EPSG code for the desired projection.
        Do not include 'EPSG'
        if crs_epsg== None, the projection will be estimated based on the longitude
    """
    color_palettes = {10:'tab10',20:'tab20'}
    wgs=pyproj.Proj("EPSG:4326")
    def __init__(self, table_name, top_left_lat, top_left_lon, 
                 cell_size=100, nrows=20, ncols=20, rotation=0, crs_epsg=None ,quietly=False):
        if not check_table_name(table_name):
            new_table_name = normalize_table_name(table_name)
            if not quietly:
                print(f'Incorrect table name "{table_name}", using "{new_table_name}" instead')
            warn(f'Incorrect table name "{table_name}", using "{new_table_name}" instead')
            table_name = new_table_name

        if crs_epsg is None:
            utm_zone = int(np.floor((top_left_lon + 180) / 6) + 1)
            crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        else:
            crs = f"EPSG:{crs_epsg}"

        super(Grid_maker, self).__init__(
                table_name, 
                quietly = quietly, 
                shell_mode = True
        )

        if self.is_table():
            if not self.quietly:
                print(f'Table {self.table_name} already exists')
            warn(f'Table {self.table_name} already exists')

        if not self.quietly:
            print('Calculating initial coordinates of each cell')
        EARTH_RADIUS_M=6.371e6
        top_left_lon_lat={'lon': top_left_lon, 'lat': top_left_lat}
        bearing=(90-rotation+360)%360
        self.projection=pyproj.Proj(crs)
        cell_size=cell_size
        self.nrows=nrows
        self.ncols=ncols
        Ad=(cell_size*ncols)/EARTH_RADIUS_M
        la1=deg_to_rad(top_left_lon_lat['lat'])
        lo1=deg_to_rad(top_left_lon_lat['lon'])
        bearing_rad=deg_to_rad(bearing)
        la2= math.asin(math.sin(la1) * math.cos(Ad)  + 
                          math.cos(la1) * math.sin(Ad) * math.cos(bearing_rad))
        lo2= lo1+ math.atan2(math.sin(bearing_rad) * math.sin(Ad) * math.cos(la1),
                             math.cos(Ad)-math.sin(la1)*math.sin(la2))
        top_right_lon_lat={'lon': rad_to_deg(lo2), 'lat': rad_to_deg(la2)}        
        top_left_xy=pyproj.transform(self.wgs, self.projection, 
                                     top_left_lon_lat['lat'],top_left_lon_lat['lon'])
        top_right_xy=pyproj.transform(self.wgs, self.projection, 
                                      top_right_lon_lat['lat'],top_right_lon_lat['lon'])
        # now we have the top two points in a spatial system, 
        # we can calculate the rest of the points
        dydx=(top_right_xy[1]-top_left_xy[1])/(top_right_xy[0]-top_left_xy[0])
        theta=math.atan((dydx))
        cosTheta=math.cos(theta)
        sinTheta=math.sin(theta)
        x_unRot=[j*cell_size for i in range(nrows) for j in range(ncols)]
        y_unRot=[-i*cell_size for i in range(nrows) for j in range(ncols)]
        # use the rotation matrix to rotate around the origin
        x_rot=[x_unRot[i]*cosTheta -y_unRot[i]*sinTheta for i in range(len(x_unRot))]
        y_rot=[x_unRot[i]*sinTheta +y_unRot[i]*cosTheta for i in range(len(x_unRot))]
        x_rot_trans=[top_left_xy[0]+x_rot[i] for i in range(len(x_rot))]
        y_rot_trans=[top_left_xy[1]+y_rot[i] for i in range(len(x_rot))]
        lat_grid, lon_grid=pyproj.transform(self.projection,self.wgs,x_rot_trans, y_rot_trans)

        if not self.quietly:
            print('Defining properties and headers')
        self.grid_coords_ll=[[lon_grid[i], lat_grid[i]] for i in range(len(lon_grid))]
        self.grid_coords_xy=[[x_rot_trans[i], y_rot_trans[i]] for i in range(len(y_rot_trans))]
        self.properties={'color':[0,0,0],
                        'height': 0,
                        'id': 0, 
                        'interactive': "Web",
                        'name': "test"}
        try:
            tz = get_timezone_offset(top_left_lat,top_left_lon)
        except Exception:
            warn('Could not set timezone.')
            warn(traceback.format_exc())
            tz = -5
        self.header={
            'cellSize': cell_size,
            'latitude': top_left_lat,
            'longitude': top_left_lon,
            'ncols': ncols,
            'nrows': nrows,
            'projection': '+proj=lcc +lat_1=42.68333333333333 +lat_2=41.71666666666667 +lat_0=41 +lon_0=-71.5 +x_0=200000 +y_0=750000 +ellps=GRS80 +datum=NAD83 +units=m +no_def', #not sure from where?
            'rotation': rotation,
            'tableName':self.table_name,
            'tz': tz
        }
        self.geojson_object = None

    def generate_geogriddata(self):
        '''
        Ensures that all cells point to a valid cell type in the features endpoint.
        '''
        types_list = list(self.geojson_object['properties']['types'].keys())
        for cell in self.geojson_object['features']:
            cell_type = cell['properties']['name']
            if cell_type != 'None':
                if cell_type not in types_list:
                    cell_type = np.random.choice(types_list)
                    cell['properties']['name'] = cell_type
                type_props = self.geojson_object['properties']['types'][cell_type]
                cell['properties']['height'] = type_props['height']
                type_color = type_props['color']
                if type(type_color) is str:
                    cell['properties']['color']  = hex_to_rgb(type_color)
                else:
                    cell['properties']['color']  = type_color
            else:
                if 'interactive' in cell['properties'].keys():
                    del cell['properties']['interactive']
                cell['properties']['color'] = [0,0,0,0]
                cell['properties']['height'] = 0

    def choose_color(self,i,n):
        '''
        Uses matplotlib tab10 and tab20 color palettes to generate a color.

        Parameters
        ----------
        i: int
            Index of color (e.g. 0,1,2,3,...,n)
        n: int
            Size of palette

        Returns
        -------
        color: list
            RGB code for color
        '''
        if n<=10:
            cmap = matplotlib.cm.get_cmap('tab10')
            mod = 10
        else:
            cmap = matplotlib.cm.get_cmap('tab20')
            mod = 20
        return [int(c*255) for c in cmap.colors[i % mod]]

    def generate_color(self):
        '''
        Uses default color palette to generate colors for all types that do not have a color defined.
        '''
        types_missing_color = [k for k in self.get_grid_geojson()['properties']['types'] if 'color' not in self.get_grid_geojson()['properties']['types'][k].keys()]
        n = len(types_missing_color)
        i = 0
        for k in types_missing_color:
            self.geojson_object['properties']['types'][k]['color'] = self.choose_color(i,n)
            i+=1

    def generate_height(self):
        '''
        Adds height zero to types missing height
        '''
        for k in self.get_grid_geojson()['properties']['types']:
            if 'height' not in self.geojson_object['properties']['types'][k].keys():
                self.geojson_object['properties']['types'][k]['height'] = 0

    def generate_interactive(self):
        '''
        Adds the interactive=Web property when missing
        '''
        for k in self.get_grid_geojson()['properties']['types']:
            if 'interactive' not in self.geojson_object['properties']['types'][k].keys():
                self.geojson_object['properties']['types'][k]['interactive'] = 'Web'

    def generate_missing(self):
        '''
        Wrapper to generate missing necessary properties: color and height
        '''
        self.generate_color()
        self.generate_height()
        self.generate_interactive()
        self.generate_geogriddata()

    def get_grid_geojson(self):
        '''
        Returns the object created with :func:`brix.Grid_maker.set_grid_geojson`.
        If the object has not been created, it will created using the default properties.

        Returns
        -------
        geogrid: dict
            Object to be posted to GEOGRID endpoint to create table. 
            See :func:`brix.commit_grid`
        '''
        if self.geojson_object is None:
            self.set_grid_geojson()
        return self.geojson_object

    def set_grid_geojson(self, add_properties={}, include_global_properties=True):
        '''
        Takes the pre-computed locations of the top-left corner of every grid cell and creates a corresponding Multi-Polygon geojson object.
        Does not return the object, but saves it in object.
        Use :func:`brix.Grid_maker.get_grid_geojson` to access it


        Parameters
        ----------
        add_properties: dict (optional)
            Properties of each type.
            Currently not supported
        include_global_properties: Boolean, defaults to `True`
            If `True` it will add global properties to each cell. 
        '''
        if not self.quietly:
            print('Generating grid geojson')
        dLLdCol=[self.grid_coords_ll[1][0]-self.grid_coords_ll[0][0], 
                         self.grid_coords_ll[1][1]-self.grid_coords_ll[0][1]]
        dLLdRow=[self.grid_coords_ll[self.ncols][0]-self.grid_coords_ll[0][0], 
                       self.grid_coords_ll[self.ncols][1]-self.grid_coords_ll[0][1]]
        features=[]
        for i, g in enumerate(self.grid_coords_ll):
            coords=[g, 
                    [g[0]+dLLdRow[0], g[1]+dLLdRow[1]],
                    [g[0]+dLLdCol[0]+dLLdRow[0], g[1]+
                     dLLdCol[1]+dLLdRow[1]],
                    [g[0]+dLLdCol[0],g[1]+dLLdCol[1]], 
                    g]
            properties={}
            properties=copy.copy(self.properties)
            properties['id'] = i
            # for p in self.properties:
            #     properties[p]=self.properties[p][i]
            # for p in add_properties:
            #     properties[p]=add_properties[p][i]
            features.append({'type': 'Feature',
                             'geometry':{'type': 'Polygon', 'coordinates': [coords]},
                             'properties': properties})
        geojson_object={'type': 'FeatureCollection',
                        'features': features}
        if include_global_properties:
            type_attributes = {
                'LBCS': [{'proportion':1,'use':{}}],
                'NAICS':[{'proportion':1,'use':{}}],
                'color':[0,0,0],
                'height': 0,
                'interactive': "Web", 
                'name': 'test',
                'tableData': {'id': 0}
              }
            geojson_object['properties']={ 
                'geogrid_to_tui_mapping': { },
                'header': self.header,
                'types' : {'Default': type_attributes}
            }
        self.geojson_object = geojson_object
    
    def plot(self):
        '''
        Plots the whole grid in blue. 
        If some cells are maked as interactive, they will be plotted in red.
        Useful to ensure the correct behavior. 
        '''
        plt.scatter([g[0] for g in self.grid_coords_ll], 
            [g[1] for g in self.grid_coords_ll], c='blue', alpha=0.5)
        plt.show()

    def commit_grid(self):
        '''
        Commits the geogrid to create the new table.
        This will reset GEOGRIDDATA and clear all indicator endpoints if the table alread existed.
        '''
        post_table = True
        if self.is_table():
            post_table = input('Table exists, do you want to overwrite it?')
            post_table = (post_table.lower().strip()[0]=='y')
        if post_table:
            self.generate_missing()
            geogrid = self.get_grid_geojson()
            r = requests.post(self.cityIO_post_url, data = json.dumps({'GEOGRID':geogrid}), headers=self.post_headers)
            if not self.quietly:
                print('Geogrid posted to:')
                print(r.url)
                print(r.status_code)
            self.reset_geogrid_data()
            self.clear_endpoints()
            if not self.quietly:
                print(self.front_end_url)
        else:
            if not self.quietly:
                print("Table not overwritten")

    def edit_types(self,types):
        '''
        Changes the default types for user defined types.
        If the GEOGRID object returned has not been created, it will created using the default properties.

        Parameters
        ----------
        types: dict or list
            Object with new type definitions.
            When passing a dict, each type name is passed as a key and values are dicts with the properties of each type. 
            When passing a list, only passes the names of the types, other baseline properties will be generated by default.
        '''
        if self.geojson_object is None:
            self.set_grid_geojson()
        if type(types) is dict:
            self.geojson_object['properties']['types']=types
        elif type(types) is list:
            self.geojson_object['properties']['types']={k:{} for k in types}
            self.generate_missing()
        else:
            raise NameError(f"Wrong type definition, pass dict or list, object passed was {type(types)}")

    def grid_types(self):
        return self.geojson_object['properties']['types']

    def set_noninteractive(self,poly):
        '''
        Sets cells that fall outside of polygon as non interactive.
        
        Parameters
        ----------
        poly: shapely Polygon
            Polygon bounding the interactive part of the grid.
        '''
        if self.geojson_object is None:
            self.set_grid_geojson()
        for cell in self.geojson_object['features']:
            cell_shape = shape(cell['geometry'])
            if not cell_shape.centroid.within(poly):
                cell['properties']['name'] = 'None'
                cell['properties']['color'] = [0,0,0,0]
                cell['properties'].pop('interactive',None)

def grid_from_poly(table_name,poly,ncells=20):
    '''
    Creates a :class:`brix.Grid_maker` object based on the given polygon.
    It sets cells that fall outside the polygon as non-interactive.

    Parameters
    ----------
    table_name: str
        Name of table to create.
        It will overwrite it if it exists.
    poly: shapely.Polygon
        Polygon of grid bounds. 
    ncells: int, defaults to 20
        Number of cells in the longest side.

    Returns
    -------
    G: :class:`brix.Grid_maker`
        Grid_maker object with properties inferrred from polygon.
    '''

    rotation = 0
    corner_bbox = poly.bounds #lower left corner and upper right corner

    ## DEFINE PARAMETS OF THE GRID ##
    top_left_lat = corner_bbox[3] ## #42.3664655 
    top_left_lon = corner_bbox[0] ## #-71.0854323
    top_left = (top_left_lat,top_left_lon)

    top_right_lat = corner_bbox[3]
    top_right_lon = corner_bbox[2]
    top_right = (top_right_lat,top_right_lon)

    bottom_left_lat = corner_bbox[1]
    bottom_left_lon = corner_bbox[0]
    bottom_left = (bottom_left_lat,bottom_left_lon)

    dist_horizontal = vincenty(top_left, top_right)*1000 #in m
    dist_vertical = vincenty(top_left, bottom_left)*1000 #in m

    if dist_horizontal > dist_vertical:
        ncols = ncells ##
        cell_side = round(dist_horizontal / ncols)
        cell_size = cell_side #m ##
        nrows = round(dist_vertical / cell_side) ##
    else:
        nrows = ncells ##
        cell_side = round(dist_vertical / nrows)
        cell_size = cell_side #m ##
        ncols = round(dist_horizontal / cell_side) ##

    G = Grid_maker(table_name, top_left_lat, top_left_lon, rotation=rotation, cell_size=cell_size, nrows=nrows, ncols=ncols)
    G.set_grid_geojson()
    G.set_noninteractive(poly)

    return G