#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 18:57:59 2019

@author: doorleyr
@contributors: crisjf, guadalupebabio
"""
from .classes import Handler
from .helpers import deg_to_rad,rad_to_deg, get_timezone_offset
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
from warnings import warn

class Grid(Handler):
    wgs=pyproj.Proj("EPSG:4326")
    def __init__(self, table_name, top_left_lat, top_left_lon, 
                 cell_size=100, nrows=20, ncols=20, rotation=0, crs_epsg=None ,quietly=False):
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

        super(Grid, self).__init__(
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

    def get_grid_geojson(self):
        '''
        Returns the object created with :func:`brix.Grid.set_grid_geojson`.
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
        Use :func:`brix.Grid.get_grid_geojson` to access it


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

    def edit_types(types_json):
        '''
        Changes the default types for user defined types.
        If the GEOGRID object returned has not been created, it will created using the default properties.

        Parameters
        ----------
        types_json: dict
            Object with new type definitions.
            Each type name is passed as a key and values are dicts with the properties of each type. 
        '''
        if self.geojson_object is None:
            self.set_grid_geojson()
        self.geojson_object['properties']['types']=types_json
