#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 18:57:59 2019

@author: doorleyr
"""
import pyproj
import math
import numpy as np
import matplotlib.path as mplPath
import requests
import matplotlib.pyplot as plt

def deg_to_rad(deg):
    return deg*math.pi/180

def rad_to_deg(rad):
    return rad*180/math.pi

def point_in_shape(point, geometry):
    if geometry['type']=='MultiPolygon':
        for polygon in geometry['coordinates'][0]:
            bbPath = mplPath.Path(polygon)
            if bbPath.contains_point((point[0],point[1])):
                return True
        return False
    else:
        bbPath = mplPath.Path(geometry['coordinates'][0])
        if bbPath.contains_point((point[0],point[1])):
            return True
        else:
            return False
            
#def flip_geojson_vertical(geojson, n_rows, n_cols):
#    new_features=[]
#    for row in reversed(range(n_rows)):
#        new_features.extend(geojson['features'][row*ncols: (row+1)*ncols])
#    geojson['features']=new_features
#    return geojson
        
            

wgs=pyproj.Proj("+init=EPSG:4326")

class Grid():
    def __init__(self, top_left_lon, top_left_lat, rotation, crs_epsg, 
                 cell_size, nrows, ncols, flip_y=False):
        """
        Takes the properties of the grid and using the Haversine formula, 
        computes the location of the top-right corner. Then projects
        to spatial coordinates in order to find the locations of the rest of 
        the grid cells
        """
        EARTH_RADIUS_M=6.371e6
        top_left_lon_lat={'lon': top_left_lon, 'lat': top_left_lat}
        bearing=(90-rotation+360)%360
        self.projection=pyproj.Proj("+init=EPSG:"+crs_epsg)
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
        top_left_xy=pyproj.transform(wgs, self.projection,top_left_lon_lat['lon'], 
                                     top_left_lon_lat['lat'])
        top_right_xy=pyproj.transform(wgs, self.projection,top_right_lon_lat['lon'], 
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
        lon_grid, lat_grid=pyproj.transform(self.projection,wgs,x_rot_trans, y_rot_trans)
        self.grid_coords_ll=[[lon_grid[i], lat_grid[i]] for i in range(len(lon_grid))]
        self.grid_coords_xy=[[x_rot_trans[i], y_rot_trans[i]] for i in range(len(y_rot_trans))]
        self.properties={'tui_id': [None for g in lon_grid],
                         'interactive':[True for g in lon_grid]}
        self.geogrid_to_tui_mapping={}
        self.header={'longitude': top_left_lon,
            'latitude': top_left_lat,
            'ncols':ncols,
            'nrows': nrows,
            'cellSize': cell_size,
            'rotation': rotation}
    
    def flip_tui_ids_y(self):
        new_tui_ids=[]
        new_tui_mapping={}
        for row in reversed(range(self.nrows)):
            new_tui_ids.extend(self.properties['tui_id'][row*self.ncols: (row+1)*self.ncols])
        for grid_cell_id in range(len(new_tui_ids)):
            if new_tui_ids[grid_cell_id] is not None:
                new_tui_mapping[grid_cell_id]=  new_tui_ids[grid_cell_id]
        self.properties['tui_id']=new_tui_ids
        self.geogrid_to_tui_mapping=new_tui_mapping
        
    def add_tui_interactive_cells(self, tui_top_left_row_index, tui_top_left_col_index,
                                  tui_num_interactive_rows, tui_num_interactive_cols):
        """
        takes an initialised grid which defines the full model area
        assigns a portion of the rows and coolumsn to be TUI interactive cells
        the  interactive cells are maked as interactive and given a grid_data_id
        corresponding to their order in the interactive grid.
        
        """    
        
        tui_ind=0
        for r in range(tui_top_left_row_index, tui_top_left_row_index+tui_num_interactive_rows):
            for c in range(tui_top_left_col_index, tui_top_left_col_index+tui_num_interactive_cols):
                geogrid_index=r*self.ncols+c
                self.properties['tui_id'][geogrid_index]=tui_ind
                self.geogrid_to_tui_mapping[geogrid_index]=tui_ind
                tui_ind+=1
        
#    def extend_int_grid_to_full(self, col_margin_left,  row_margin_top, cell_width, 
#                                         cell_height):
#        """
#        takes an initialised grid which defines an interactive area
#        adds additional rows and columns in order to create a full_grid area
#        the original interactive cells are maked as interactive and given a grid_data_id
#        corresponding to their order in the interactive grid.
#        
#        """
#        dXYdCol=np.array([self.grid_coords_xy[1][0]-self.grid_coords_xy[0][0], 
#                         self.grid_coords_xy[1][1]-self.grid_coords_xy[0][1]])
#        dXYdRow=np.array([dXYdCol[1], -dXYdCol[0]]) # rotate the vector 90 degrees
#        int_grid_origin=np.array(self.grid_coords_xy[0])
#        full_grid_origin=int_grid_origin-row_margin_top*dXYdRow-col_margin_left*dXYdCol
#        full_grid_points=np.array([full_grid_origin+j*dXYdCol+i*dXYdRow for i in range(
#                cell_height) for j in range(cell_width)])
#        self.original_rows=list(range(row_margin_top, row_margin_top+self.nrows))
#        self.original_cols=list(range(col_margin_left, col_margin_left+self.ncols))
#        orginal_cell_flag=[True if (cell_num%cell_width in self.original_cols and 
#                                    int(cell_num/cell_width) in self.original_rows
#                                    ) else False for cell_num in range(len(full_grid_points))]
#        int_id=0
#        interactive_ids=[]
#        for ocf in orginal_cell_flag:
#            if ocf:
#                interactive_ids.append(int_id)
#                int_id+=1
#            else:
#                interactive_ids.append(None)
#        self.grid_coords_xy=list(full_grid_points)
#        lon_grid, lat_grid=pyproj.transform(self.projection,wgs,
#                                            full_grid_points[:,0],full_grid_points[:,1])
#        self.grid_coords_ll=[[lon_grid[i], lat_grid[i]] for i in range(len(lon_grid))]
#        self.properties['interactive']= orginal_cell_flag
#        self.properties['interactive_id']= interactive_ids
#        self.int_to_meta_map={int(interactive_ids[i]):i for i in 
#                       range(len(interactive_ids)) if interactive_ids[i] is not None}
#        self.ncols=cell_width
#        self.nrows=cell_height
        
    def get_land_uses(self, lu_geojson, lu_property):
        """
        Takes a grid with interactive and static cells
        Cross-references each cell to a geojson file of land-use polygons
        Assigns each cell to a land-use
        """
        land_use=["None"]*len(self.grid_coords_ll)
        for cell_num in range(len(self.grid_coords_ll)):
            for lu_feature in lu_geojson['features']:
                if point_in_shape(self.grid_coords_ll[cell_num], lu_feature['geometry']):
                    land_use[cell_num]=lu_feature['properties'][lu_property]
        self.properties['land_use']=land_use

    def get_grid_geojson(self, add_properties={}, include_global_properties=True):
        """
        Takes the pre-computed locations of the top-left corner of every grid cell
        and creates a corresponding Multi-Polygon geojson object
        """
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
            for p in self.properties:
                properties[p]=self.properties[p][i]
            for p in add_properties:
                properties[p]=add_properties[p][i]
            features.append({'type': 'Feature',
                             'geometry':{'type': 'Polygon', 'coordinates': [coords]},
                             'properties': properties})
        geojson_object={'type': 'FeatureCollection',
                        'features': features}
        if include_global_properties:
            geojson_object['properties']={
                                'geogrid_to_tui_mapping': self.geogrid_to_tui_mapping,
                                'header': self.header}
        return geojson_object
    
    def plot(self):
        """
        Plots the whole grid in blue. 
        If some cells are maked as interactive, they will be plotted in red.
        """
        plt.scatter([g[0] for g in self.grid_coords_ll], 
            [g[1] for g in self.grid_coords_ll], c='blue', alpha=0.5)
        if 'tui_id' in self.properties:
            plt.scatter([self.grid_coords_ll[g][0] for g in range(len(self.grid_coords_ll)
                        ) if self.properties['tui_id'][g] is not None], 
                        [self.grid_coords_ll[g][1] for g in range(len(self.grid_coords_ll)
                        ) if self.properties['tui_id'][g] is not None], 
                        c='red', alpha=0.5)
        plt.show()
        



