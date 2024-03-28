import streamlit as st
import numpy as np
import pandas as pd
import pickle
import folium
from streamlit_folium import st_folium

import commuting_model as como
import cowork_locations as coloc
import visualization_utils as wizard

# This code performs and visualizes computations related to commuting and coworking locations, presenting a heatmap of improvements in commuting with additional coworking spaces based on user-selected input. The application includes options for recalculation, visualization, and CSV download, contingent upon certain input conditions.


st.title('RealWork-WebApp', anchor=None)
st.header('HeatMap', anchor=None)
st.markdown('Es wurde für jeden zusätzlichen CWS im Kandidatenset\
            die Zielfunktion evaluiert und eine entsprechende Färbung\
            vorgenommen:')

#Überprüfen der Vorraussetzungen
if 'base_solution' in st.session_state:
    with st.form("my_form"):
        submitted = st.form_submit_button("Neuberechnung")
        
        if submitted:        
            with st.spinner("Im Folgenden wird die Berechnung durchgeführt. Dies kann einige **wenige Minuten** dauern."):
                progress_text = f"Die Berechnung durchgeführt. Dies kann einige **wenige Minuten** dauern."
                my_bar = st.progress(0, text=progress_text)
                res_hm = coloc.heatmap(st.session_state["selected_counties"],
                                    st.session_state["existing_cws"],
                                    progress = my_bar)
                st.session_state['res_hm'] = res_hm
                st.markdown('Berechnung abgeschlossen.')    
    
    if 'res_hm' in st.session_state:
        #Ausgabe der Visualisierung
        st.subheader("Visualisierung:")
        with st.form("vis_form"):
            submitted = st.form_submit_button("Visualisierung")
            if submitted:   
                m = wizard.plot_heatmap(st.session_state['res_hm'],
                                    st.session_state["region_df"])
                
                st_data = st_folium(m, width=725, key = hash(3423))
        #Download-Area
        st.subheader("Download")
        df = st.session_state['res_hm'][["LAU_ID", "LAU", "Improvement"]]
        df.rename(columns={'LAU_ID': 'AGS', 'LAU': 'Gemeinde', 'Improvement': 'Verbesserung'}, 
                inplace = True)
        df.set_index('AGS', inplace = True)
        csv = df.to_csv().encode('utf-8')
        st.download_button("CSV-Download",csv,
                        "Ergebnis_Heatmap.csv","text/csv",
                        key='download-hm-csv')
else:
    st.markdown(f"**Diese Seite steht erst zur Verfügung,\
        wenn die Eingaben auf der Startseite getätigt wurden.**")
