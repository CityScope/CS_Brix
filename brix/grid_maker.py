#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 18:57:59 2019

@author: doorleyr
@contributors: crisjf, guadalupebabio
"""
from .classes import Handler
from .helpers import deg_to_rad,rad_to_deg
from .functions import normalize_table_name, check_table_name

import pyproj
import math
import numpy as np
import matplotlib.path as mplPath
import requests
import matplotlib.pyplot as plt
import copy
import json
from warnings import warn


class Grid():
    wgs=pyproj.Proj("EPSG:4326")
    def __init__(self, table_name, top_left_lon, top_left_lat, rotation, crs_epsg, 
                 cell_size, nrows, ncols, flip_y=False):
        """
        Takes the properties of the grid and using the Haversine formula, 
        computes the location of the top-right corner. Then projects
        to spatial coordinates in order to find the locations of the rest of 
        the grid cells

        Parameters
        ----------
        crs_epsg: str
            EPSG code for the desired projection.
            Do not include 'EPSG'


        """
        if not check_table_name(table_name):
            new_table_name = normalize_table_name(table_name)
            print(f'Incorrect table name "{table_name}", using "{new_table_name}" instead')
            warn(f'Incorrect table name "{table_name}", using "{new_table_name}" instead')
            table_name = new_table_name
        EARTH_RADIUS_M=6.371e6
        top_left_lon_lat={'lon': top_left_lon, 'lat': top_left_lat}
        bearing=(90-rotation+360)%360
        self.projection=pyproj.Proj(f'EPSG:{crs_epsg}')
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
        top_left_xy=pyproj.transform(self.wgs, self.projection,top_left_lon_lat['lon'], 
                                     top_left_lon_lat['lat'])
        top_right_xy=pyproj.transform(self.wgs, self.projection,top_right_lon_lat['lon'], 
                                      top_right_lon_lat['lat'])
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
        lon_grid, lat_grid=pyproj.transform(self.projection,self.wgs,x_rot_trans, y_rot_trans)
        self.grid_coords_ll=[[lon_grid[i], lat_grid[i]] for i in range(len(lon_grid))]
        self.grid_coords_xy=[[x_rot_trans[i], y_rot_trans[i]] for i in range(len(y_rot_trans))]
        self.properties={'color':[0,0,0],
                        'height': 0,
                        'id': 0, 
                        'interactive': "Web",
                        'name': "test"}
        self.header={'cellSize': cell_size,
            'latitude': top_left_lat,
            'longitude': top_left_lon,
            'ncols':ncols,
            'nrows': nrows,
            'projection': '+proj=lcc +lat_1=42.68333333333333 +lat_2=41.71666666666667 +lat_0=41 +lon_0=-71.5 +x_0=200000 +y_0=750000 +ellps=GRS80 +datum=NAD83 +units=m +no_def', #not sure from where?
            'rotation': rotation,
            'tableName':table_name,
            'tz': -5 
            }

    def get_grid_geojson(self, add_properties={}, include_global_properties=True):
        '''
        Takes the pre-computed locations of the top-left corner of every grid cell
        and creates a corresponding Multi-Polygon geojson object

        Parameters
        ----------
        add_properties: dict (optional)
            Properties of each type.
            Currently not supported
        include_global_properties: Boolean, defaults to `True`
            If `True` it will add global properties to each cell. 

        Returns
        -------
        geogrid: dict
            Object to be posted to GEOGRID endpoint to create table. 
            See :func:`brix.commit_grid`
        '''
        dLLdCol=[self.grid_coords_ll[1][0]-self.grid_coords_ll[0][0], 
                         self.grid_coords_ll[1][1]-self.grid_coords_ll[0][1]]
        dLLdRow=[self.grid_coords_ll[self.ncols][0]-self.grid_coords_ll[0][0], 
                       self.grid_coords_ll[self.ncols][1]-self.grid_coords_ll[0][1]]
        features=[]      
        print(self.grid_coords_ll) 
        for i, g in enumerate(self.grid_coords_ll):
            coords=[g, 
                    [g[0]+dLLdRow[0], g[1]+dLLdRow[1]],
                    [g[0]+dLLdCol[0]+dLLdRow[0], g[1]+
                     dLLdCol[1]+dLLdRow[1]],
                    [g[0]+dLLdCol[0],g[1]+dLLdCol[1]], 
                    g]
            properties={}
            print(self.properties)
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
        return geojson_object
    
    def plot(self):
        '''
        Plots the whole grid in blue. 
        If some cells are maked as interactive, they will be plotted in red.
        Useful to ensure the correct behavior. 
        '''
        plt.scatter([g[0] for g in self.grid_coords_ll], 
            [g[1] for g in self.grid_coords_ll], c='blue', alpha=0.5)

        plt.show()

def commit_grid(table_name, geogrid):
    '''
    Commits the geogrid to create the new table.
    This will reset GEOGRIDDATA and clear all indicator endpoints if the table alread existed.
    
    Parameters
    ----------
    table_name: str
        Name of table to create.
    geogrid: dict
        GEOGRID object returned by :func:`brix.Grid.get_grid_geojson`
    '''
    if not check_table_name(table_name):
        new_table_name = normalize_table_name(table_name)
        print(f'Incorrect table name "{table_name}", using "{new_table_name}" instead')
        warn(f'Incorrect table name "{table_name}", using "{new_table_name}" instead')
        table_name = new_table_name
    H = Handler(table_name, shell_mode=True)
    r = requests.post(H.cityIO_post_url, data = json.dumps({'GEOGRID':geogrid}), headers=Handler.cityio_post_headers)
    print('Geogrid posted to:')
    print(r.url)
    print(r.status_code)
    H.reset_geogrid_data()
    H.clear_endpoints()


def edit_types(geogrid, types_json):
    '''
    Changes the default types for user defined types.

    Parameters
    ----------
    geogrid: dict
        GEOGRID object returned by :func:`brix.Grid.get_grid_geojson`
    types_json: dict
        Object with new type definitions.
        Each type name is passed as a key and values are dicts with the properties of each type. 
    '''
    geogrid['properties']['types']=types_json
