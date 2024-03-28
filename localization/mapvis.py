import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import pickle 
import os
import sys
from importlib import reload


# This part of the code facilitates the visualization of geographical data using the geopandas, contextily, and matplotlib libraries, allowing users to add basemaps, plot geographic shapes, highlight specific areas, create choropleth maps, add points, highlight major cities, and annotate the visualization.



# sys.path.append('../co2work/code/localization')
# from code.localization.commuting_model import commuting_model as cm

# set filepath to your processed .shp geodata files
_shapedf = gpd.read_file('XXX.shp',
                              dtype = {'LAU_ID': str})
_shapedf = _shapedf.to_crs(epsg=3857)

# set filepath to your processed .shp MunicipalPoints files
_coords = gpd.read_file('XXX.shp')
_coords = _coords.set_index(['AGS'])
_coords = _coords.to_crs(epsg=3857)   

class mapvis:
    
    def __init__(self):
        self.f, self.ax = plt.subplots(1, figsize=(12, 12))
        self.ax.axis('off')
        self.linewidth = 0.7
        self.edgecolor = 'lightgrey'
        
    def add_basemap(self):
        ctx.add_basemap(self.ax, source = ctx.providers.OpenStreetMap.DE)
        
    def background(self, l_ags):
        assert len(l_ags), f"An empty list was inputted."
        which = [ags.startswith(tuple(l_ags)) for ags in _shapedf['LAU_ID']]
        _shapedf[which].exterior.plot(ax=self.ax,
                                      linewidth=self.linewidth,
                                      edgecolor=self.edgecolor)
        pass
    
    def highlight(self, l_ags, color='C0', alpha=1):
        assert len(l_ags), f"An empty list was inputted."
        which = [ags.startswith(tuple(l_ags)) for ags in _shapedf['LAU_ID']]        
        _shapedf[which].plot(ax=self.ax, color = color, alpha = alpha,
                             linewidth=self.linewidth,
                             edgecolor=self.edgecolor)
        pass
    
    def highlight_area(self, l_ags, color='C0', alpha=1):
        assert len(l_ags), f"An empty list was inputted."
        which = [ags.startswith(tuple(l_ags)) for ags in _shapedf['LAU_ID']]
        area = _shapedf[which].dissolve(by='CNTR_CODE') #CNTR_CODE is constant thereofre all is merged into one  
        area.plot(ax=self.ax, color = color, alpha = alpha,
                             linewidth=self.linewidth,
                             edgecolor=self.edgecolor)
        pass
    
    def choroplet(self, l_ags, variable, **kwargs):
        toplotdf = _shapedf.merge(variable, left_on = "LAU_ID", right_index = True)
        toplotdf.plot(ax=self.ax, column = variable.name, alpha = .5, 
                      legend = True,
                      linewidth=self.linewidth, edgecolor=self.edgecolor)       
        pass
        
    
    def add_points(self, l_ags, **kwargs):
        assert len(l_ags), f"An empty list was inputted."
        #points = #pd.DataFrame([model.get_coord(ags) for ags in l_ags],
        #                      columns = ['latitude', 'longitude'])
        points = _coords.loc[l_ags]
        #points = gpd.points_from_xy(points.longitude, points.latitude,
        #                            crs="EPSG:4326")
            
        #points = gpd.GeoSeries(points).to_crs(epsg=3857)
        points.plot(ax=self.ax, **kwargs)
        pass
    
       
    def major_cities(self, l_ags):
        assert len(l_ags), f"An empty list was inputted."
        which = [ags.startswith(tuple(l_ags)) for ags in _shapedf['LAU_ID']]
        points =  _shapedf[which]['geometry'].representative_point()     
        points.plot(ax=self.ax, marker='o', color='red', markersize=50)
        
    def annotate(self, points):                   
        points.plot(ax=self.ax, marker='o', color='red', markersize=50)
        
    def legend(self):
        #legend_lon, legend_lat = 10.26930750607687, 54.482829173990936
        #legendanchor = gpd.GeoDataFrame(geometry=gpd.points_from_xy([legend_lon], [legend_lat]))
        #legendanchor.crs = 'epsg:4326'     
        #legendanchor = legendanchor.to_crs('epsg:3857')
        #legend_x, legend_y = legendanchor.geometry.iloc[0].x, legendanchor.geometry.iloc[0].y
        #print(f"Legende = {legend_x}, {legend_y}")
        self.f.legend(loc = 'upper right', bbox_to_anchor=(.85, .75))
        #self.f.legend(loc = 'upper right')
