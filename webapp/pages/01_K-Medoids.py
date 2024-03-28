import os
import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle
import folium
from streamlit_folium import st_folium

import commuting_model
import cowork_locations
import visualization_utils
from importlib import reload

# reloading own modules
from importlib import reload
reload(commuting_model); reload(cowork_locations);reload(visualization_utils)
import commuting_model as como
import cowork_locations as coloc
import visualization_utils as wizard


# The code utilises the K-Medoids algorithm for coworking space (CWS) placement optimization, allowing users to input parameters such as the number of new CWS to be placed, seed for result reproducibility, and visualizing the results, including potential time savings and commuters addressed.

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))

st.title('RealWork-WebApp', anchor=None)
st.header('K-Mediods Algorithmus', anchor=None)

st.markdown(open(ROOT_DIR + '/webapp/texts/kmed_desc.md').read(),
            unsafe_allow_html=True)

#Überprüfen der Vorraussetzungen
if 'base_solution' in st.session_state:

    with st.form("my_form"):
        #Entscheidungsvariablen als Input
        #Entscheidungsvariablen als Input
        st.markdown('#### Spezifikation der Parameter / Inputs')
        
        n_tbp = st.number_input('##### Neu zu platzierende CWS',
                                value = 10, min_value=1, max_value=int(st.session_state["n_region"]/5 -st.session_state["n_exist"]),
                                help="Diese neue Anzahl an CWS soll im ausgewählten Gebiet platziert werden.")  
        
        seed = st.number_input('##### Seed',value=st.session_state['seed'], min_value=0, max_value=999999999,
                            help="Diese Zahl dient der Reproduzierbarkeit der Ergebnisse. Im Zweifel belassen Sie die Default-Eingabe.")  
        st.session_state['seed'] = seed
        
        submitted = st.form_submit_button("Bestätigung und Neuberechnung")

        if submitted:
            with st.spinner("Im Folgenden wird die Berechnung durchgeführt. Dies kann einige **wenige Minuten** dauern."):
                
                st.session_state['res_kmed'] = coloc.kLocs(**st.session_state["problem_statement"],
                                            n_cws = st.session_state['base_solution'].n_cws + n_tbp,
                                            seed = seed)
                
                # with open('.../co2work/code/pynbs/Results_K_Med.pickle', 'wb') as handle:
                #     pickle.dump(Results_K_Med, handle, protocol=pickle.HIGHEST_PROTOCOL) 

    if 'res_kmed' in st.session_state:
        # Visualisierung
        st.subheader("Ergebnisse")
        with st.form("vis_form"):
            submitted = st.form_submit_button("Visualisierung")
            if submitted:
                        
                for step, row in st.session_state['res_kmed'].iterrows():
                    st.markdown(f"Visualisierung von Schritt {step+1} mit potentiell gesparten Pesonenminuten von {row['Solution'].total_saving}:\
                                ")
                    m = wizard.plot_solution(row['Solution'], st.session_state["region_df"])
                    st_data = st_folium(m, width=725, key = step)
                    
        # Download-Area
        st.subheader("Download")
        dl_kmed = []
        for index, row in st.session_state['res_kmed'].iterrows():
            for i in range(row.Solution.n_cws):
                dl_kmed.append(
                    
                    [
                        index,
                        i,
                        row.Solution.locs[i].name,
                        row.Solution.areas[i],                                
                        row.Solution.area_savings[i],
                        row.Solution.area_commuters[i],                                                        
                    ]
                )
        dl_kmed = pd.DataFrame(dl_kmed,
                                columns = [
                                    'Schritt',
                                    'Cluster',
                                    'CWS',
                                    'Einzugsgebiet',
                                    'Pot. gesparte Personenminuten',
                                    'Pot. addressierte Pendler'
                                    ])
        dl_kmed.set_index(['Schritt', 'Cluster'], inplace = True)
        csv = dl_kmed.to_csv(float_format='%.4f').encode('utf-8')
        st.download_button("CSV-Download",csv,
                        "Ergebnis_KMedoids.csv","text/csv",
                        key='download-kmed-csv')
else:
    st.markdown(f"**Diese Seite steht erst zur Verfügung,\
        wenn die Eingaben auf der Startseite getätigt wurden.**")
