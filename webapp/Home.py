import os
import pickle
import streamlit as st
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import geopandas as gpd
import folium

import commuting_model as como
import cowork_locations as coloc
import visualization_utils
from importlib import reload
reload(visualization_utils)
import visualization_utils as wizard

# The code is based on the Streamlit web application for the Commuter-based Coworking Space Localization (CoCoLoc) project. It initializes various libraries and modules, loads geographical and demographic data, and allows users to specify parameters for the analysis, such as selected counties and existing coworking spaces. Once the user confirms their input, the code visualizes the selected regions and existing coworking spaces on a map using Folium and prompts the user to proceed with optimization on pages related to K-Medoids or Genetic Algorithm.



ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))

st.set_page_config(page_title='RealWork-WebApp')
st.title('Commuterbased Coworkingspace Localization', anchor=None)

st.markdown(open(os.path.dirname(__file__) + '/texts/covertext.md').read())

st.header('Untersuchungsgebiet', anchor=None)
st.markdown('Bitte spezifieren Sie die folgenden **Stammdaten** um das Untersuchungsgebiet zu spezifizieren:')
st.write('')

# #Session State counters and Flags
# st.session_state["Durchgang"]=0
# st.session_state["Ergebnis"]=0
# st.session_state["Visualisierung"]=0
# st.session_state["Heatmap"]=0
# st.session_state["Loaded"]=False
#Laden der Shapes and Kreise
@st.cache_data
def load_data(files):
    res0 = pd.read_csv(ROOT_DIR + files[0], dtype = {'AGS': str})
    res1 = pd.read_csv(ROOT_DIR + files[1], dtype = {'AGS': str})
    return res0, res1

county_df, municipality_df = load_data(['.../SHKreise.csv',
                                        '.../SHGemeinden.csv'])
st.session_state["municipality_df"] = municipality_df
st.session_state["county_df"] = county_df

@st.cache_data
def load_geodata(file):
    res = gpd.read_file(ROOT_DIR + file, dtype = {'LAU_ID': str})
    res = res[[e.startswith("01") for e in res['LAU_ID']]]
    res = res.reset_index()
        
    return res

shape_df = load_geodata('/data/processed/GeoData/Germany.shp')
st.session_state["shape_df"] = shape_df

if not 'seed' in st.session_state:
    st.session_state['seed'] = np.random.randint(999999)

with st.form("my_form"):
    #Entscheidungsvariablen 
    st.subheader("Spezifikation des Gebietes:")
    
    st.markdown('Bitte spezifizieren Sie die **Kreise**, deren Gemeinden das **Kandidatenset** bilden sollen:')
    selected_counties = st.multiselect('Kandidatenset:', county_df.Name,
                                       default = ['Kiel, Landeshauptstadt', 'Neumünster, Stadt','Plön', 'Rendsburg-Eckernförde'],
                                       help = "Hier kann jeder Kreis hinzugefügt werden, deren Gemeinden das Kandidatenset bilden sollen. ")

    selected_counties = tuple(county_df[county_df['Name'].isin(selected_counties)]['AGS'])
    st.session_state["selected_counties"] = selected_counties
    st.session_state["region_df"] = shape_df.loc[[lauid.startswith(selected_counties) for lauid in shape_df['LAU_ID']]].copy(deep=True)
    st.session_state["region"] = como.Municipality.dissolve(selected_counties)
    st.session_state["n_region"] = len(st.session_state["region"])
    
    
                
    st.markdown('Bitte spezifizieren Sie einzelne Gemeinden, die bereits einen **aktiven CWS** besitzen:')    
    existing_cws = st.multiselect('Bestehende CWS:', municipality_df.Name,
                                  default = ['Kiel, Landeshauptstadt', 'Gettorf','Schwentinental, Stadt', 'Preetz, Stadt',
                                   'Felde', 'Rendsburg, Stadt', 'Nortorf, Stadt', 'Neumünster, Stadt'],
                                  help="Hier kann jede Gemeinde hinzugefügt werden in der schon ein CWS exisiert.")
    existing_cws = municipality_df[municipality_df['Name'].isin(existing_cws)]['AGS']
    existing_cws = como.Municipality.get(existing_cws)
    st.session_state["existing_cws"] = existing_cws
    st.session_state["n_exist"] = len(existing_cws)
    
    problem_statement = {
    'region': selected_counties,
    'fixed_cws': existing_cws
    }
    st.session_state["problem_statement"] = problem_statement
  
    st.subheader("Bestätigen Sie die obrigen Eingaben:")
    submitted = st.form_submit_button("Bestätigung",
                                      help = "Durch Betätigung werden die obrigen Eingaben gespeichert und die weiter erforderlichen Daten im Hintergrund geladen.")
    
    if submitted:              
        
        #Plotten der Eingaben
        st.subheader("Visualisierung ihrer Eingabe:")
            
        base_solution = coloc.Solution(region = selected_counties,
                                       fixed_cws = existing_cws,
                                       locs = existing_cws)
        st.session_state['base_solution'] = base_solution
        m = wizard.plot_solution(base_solution, st.session_state["region_df"])
        
        # call to render Folium map in Streamlit
        st_data = st_folium(m, width=725)

        st.markdown("**Die Daten sind geladen**.")
        st.markdown("Für die Optimierung besuchen sie die Seiten *K-Medoids* oder *Genetischer Algorithmus*.")
