import folium
import numpy as np
import pandas as pd
import geopandas as gpd
import commuting_model as como

# This part of the code utilizes the Folium library to generate interactive maps, visualizing the results of a commuting optimization model. It includes functions to plot coworking spaces, municipalities, areas of influence, and a heatmap representing potential time savings in commuting.

def generate_colors(x):
    red, green, blue = np.random.randint(0,255, 3)
    previous = np.array([[red, green, blue]])
    color_hex = "#{:02X}{:02X}{:02X}".format(red, green, blue)
    yield color_hex
    while True:
        candidates = np.random.randint(0,255,(x,3))
        red, green, blue = candidates[np.argmax(
            [min(np.linalg.norm(candidate - previous, axis = 1)) for candidate in candidates])]
        previous = np.append(previous, np.array([[red,green,blue]]), axis = 0)
        color_hex = "#{:02X}{:02X}{:02X}".format(red, green, blue)
        yield color_hex
        
col_generator = generate_colors(100) 

def style_Einzugsgebiete(x):
    res = {
        'fillColor': next(col_generator),
        'color': 'gray'
        }
    return res

def style_Municipalities(x):
    res = {
        'fill': False,
        'color': '#BBBBBB',
        'weight': 1.5,
        }
    return res
                    
def plot_solution(solution, region_df):
    meanloc = np.mean([loc.coord for loc in solution.locs], axis = 0)
    m = folium.Map(location=meanloc, zoom_start=9) 
    
    for i, cws in enumerate(solution.fixed_cws):
        popup = folium.Popup(f"\
            <h4>{cws} <em>{(cws.ags)}</em></h4>\n\
            <dl>\
            <dt>Potentiell gesparte Personenminuten:<\dt>\
            <dd>{'{:0,.2f}'.format(solution.area_savings[i])} min </dd>\
            <dt>Potentiell angesprochene Pendler: <\dt>\
            <dd>{'{:0,.2f}'.format(solution.area_commuters[i])} Pendler</dd>\
            <\dl>\
            ", max_width = 300)
        folium.Marker(cws.coord,
                        icon=folium.Icon(color = 'lightgray'),
                        tooltip = cws,
                        popup = popup
                        ).add_to(m)      
      
    for i, cws in enumerate(solution.variable_cws):
        popup = folium.Popup(f"\
            <h4>{cws} <em>{(cws.ags)}</em></h4>\n\
            <dl>\
            <dt>Potentiell gesparte Personenminuten:<\dt>\
            <dd>{'{:0,.2f}'.format(solution.area_savings[i + solution.n_fixed])} min </dd>\
            <dt>Potentiell angesprochene Pendler: <\dt>\
            <dd>{'{:0,.2f}'.format(solution.area_commuters[i + solution.n_fixed])} Pendler</dd>\
            <\dl>\
            ", max_width = 300)
        folium.Marker(cws.coord,
                      icon=folium.Icon(color = 'blue'),
                      popup = popup,
                      tooltip = cws).add_to(m)
        
     # add municipality borders
    folium.GeoJson(
        data = region_df,
        style_function = style_Municipalities,
    ).add_to(m)        
    # add Einzugsgebiete
    def assign_cws(lau_id):
        condition = [lau_id in [mun.ags for mun in area] for area in solution.areas]
        return np.where(condition)[0][0]
    
    region_df['belongs_to'] = [assign_cws(lau_id) for lau_id in region_df['LAU_ID']]
    new_df = region_df.dissolve(by='belongs_to')   
    folium.GeoJson(
        data = new_df,
        style_function = style_Einzugsgebiete
    ).add_to(m)  
    folium.LayerControl().add_to(m)   
    
    for i, cws in enumerate(solution.locs):
        for j, mun in enumerate(solution.areas[i]):
            if mun != cws:
                popup = folium.Popup(f"\
                    <h5>{mun} <em>{(mun.ags)}</em></h5>\n\
                    <dl>\
                    <dt>Distanz zum Coworking-Space:<\dt>\
                    <dd>{'{:0,.2f}'.format(mun.get_dist(cws, disttype = 'duration'))} min </dd>\
                    <dt>Potentiell gesparte Personenminuten:<\dt>\
                    <dd>{'{:0,.2f}'.format(solution.savings[i][j])} min </dd>\
                    <dt>Potentiell angesprochene Pendler: <\dt>\
                    <dd>{'{:0,.2f}'.format(solution.commuters[i][j])} Pendler</dd>\
                    <\dl>\
                    ", max_width = 300)
                folium.CircleMarker(mun.coord,
                                    fillColor = 'black',
                                    color= None,
                                    radius = 4,
                                    popup = popup).add_to(m)
    return m


def plot_heatmap(res_heatmap, region_df):
    
    meanloc = np.mean([mun.coord for mun in res_heatmap.LAU], axis = 0)
    m = folium.Map(location=meanloc, zoom_start=9)

    folium.Choropleth(
        geo_data=region_df,
        data=res_heatmap,
        columns=["LAU_ID", "Improvement"],
        key_on="feature.properties.LAU_ID",
        fill_color="OrRd",
        fill_opacity=0.8,
        line_opacity=0.4,
        legend_name="Potentiell gesparte zusätzliche Personenminuten",
    ).add_to(m)

    folium.LayerControl().add_to(m)
    
    solexample = res_heatmap.loc[0].Solution
    for cws in solexample.fixed_cws:
        folium.Marker(cws.coord,
                        icon=folium.Icon(color = 'lightgray'),
                        tooltip = cws
                        ).add_to(m) 
         
    return m
