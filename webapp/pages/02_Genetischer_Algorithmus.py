import os
import streamlit as st
import numpy as np
import pandas as pd
import pickle
import folium
from streamlit_folium import st_folium

import commuting_model as como
import cowork_locations as coloc
import visualization_utils as wizard

# The code implements a genetic algorithm to optimize the placement of coworking spaces in selected regions based on specified parameters and constraints, allowing users to input and customize various parameters, visualize and analyze the results through interactive elements, and download the results in CSV format.


ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))

st.title('RealWork-WebApp', anchor=None)
st.header('Genetischer Algorithmus', anchor=None)

st.markdown(open(ROOT_DIR + '/webapp/texts/ga_desc.md').read(),
            unsafe_allow_html=True)

if 'base_solution' in st.session_state:    
    with st.form("my_form"):

        #Entscheidungsvariablen als Input
        st.markdown('#### Spezifikation der Parameter / Inputs')
        
        n_tbp = st.number_input('##### Neu zu platzierende CWS',
                                value = 10, min_value=1, max_value=int(st.session_state["n_region"]/5 -st.session_state["n_exist"]),
                                help="Diese neue Anzahl an CWS soll im ausgewählten Gebiet platziert werden.")  
        
        n_pop = st.number_input('##### Populationsgröße',
                                value=100, min_value=0, max_value=1000 ,
                                help="Die Populationsgröße gibt an, wieviele potentielle Konfiguartionen\
                                    gleichzeitig betrachet werden. Größere Zahlen machen den Genetischen\
                                    Algorithmus robuster, aber auch rechenintensiver.")  
        n_gen = st.number_input('##### Anzahl an Generationen',
                                value=10, min_value=0, max_value=50,
                                help="Die Anzahl an Generationen gibt an, über wieviele Generationen der genetische Algorithmus\
                                    die Population evolutionärem Druck aussetzt. Mehr Generationen führen zu besseren Ergebnissen\
                                    aber jede zusätzliche Generation führt zu immer geringeren Verbesserungen.")  
        p_survive = st.slider('##### Überlebenswahrscheinlichkeit',
                            value=0.2, min_value=0., max_value = 1., step =.05,
                            help="Die Überlebenswahrscheinlichkeit")  
        p_mut = st.slider('##### Mutationswahrscheinlichkeit',
                        value=.1, min_value=0., max_value=1., step= .05,
                        help="Diese Zahl dient der Reproduzierbarkeit der Ergebnisse. Im Zweifel belassen Sie die Default-Eingabe.")  
        
        seed = st.number_input('##### Seed',value=st.session_state['seed'], min_value=0, max_value=999999999,
                            help="Diese Zahl dient der Reproduzierbarkeit der Ergebnisse. Im Zweifel belassen Sie die Default-Eingabe.")  
        st.session_state['seed'] = seed
        
        submitted = st.form_submit_button("Bestätigung und Neuberechnung")

        if submitted:
            with st.spinner("Im Folgenden wird die Berechnung durchgeführt. Dies kann einige **wenige Minuten** dauern."):
                progress_text = f"Die bestehenden Coworking-Spaces sparen potentiell\
                    {'{:0,.2f}'.format(st.session_state['base_solution'].total_saving)}\
                    Personenminuten ein."
                my_bar = st.progress(0, text=progress_text)
                            
                res_ga = coloc.genetic_algorithm(n_pop, n_gen, p_survive, p_mut,
                                        region = st.session_state['selected_counties'],
                                        fixed_cws = st.session_state['existing_cws'],
                                        n_cws = st.session_state['n_exist'] + n_tbp,
                                        progress = my_bar,
                                        ref_saving = st.session_state['base_solution'].total_saving)
                st.session_state['res_ga'] = res_ga
                st.markdown('Berechnung abgeschlossen.')
            
    if 'res_ga' in st.session_state:       
        st.subheader("Ergebnisse")
        gen = st.number_input('Generation',
                              value=max(st.session_state['res_ga'].index.get_level_values(0)),
                              min_value=0, 
                              max_value=max(st.session_state['res_ga'].index.get_level_values(0)),
                              help="Die zu visualisierende Generation")
        # Visualisierung
        with st.form("vis_form"):
            
            
            submitted = st.form_submit_button("Visualisierung")
            
            if submitted:
                # Visualisierung der fünfbesten Ergebnisse    
                
                for i, row in st.session_state['res_ga'].iterrows():
                    sol = row.Solution
                    if not sol.check():
                        st.markdown(f"Lösung {row}: {row.CWS}, Check: {sol.check()}")
                
                for place in np.arange(1, max(st.session_state['res_ga'].index.get_level_values(1))):
                    sol = st.session_state['res_ga'].loc[gen, place].Solution
                    m = wizard.plot_solution(sol,
                                             st.session_state["region_df"])
                    st.markdown(f"Visualisierung des {place}.-besten Ergebnisses aus der {gen}. Generation\
                        mit Ersparnissen von {'{:0,.2f}'.format(sol.total_saving)} Personenminuten.\n\
                        (Verbesserung um {'{:0,.2f}'.format(sol.total_saving- st.session_state['base_solution'].total_saving)})\
                        ")          
                    st_data = st_folium(m, width=725, key = hash(str(sol)))
                    
        # Download-Area
        st.subheader("Download")
        dl_ga = []
        for index, row in st.session_state['res_ga'].iterrows():
            for i in range(row.Solution.n_cws):
                dl_ga.append(                    
                    [
                        index[0],
                        index[1],
                        i,
                        row.Solution.locs[i].name,
                        row.Solution.areas[i],                                
                        row.Solution.area_savings[i],
                        row.Solution.area_commuters[i],                                                        
                    ]
                )
        dl_ga = pd.DataFrame(dl_ga,
                             columns = [
                                 'Generation',
                                 'Platzierung',
                                 'Cluster',
                                 'CWS',
                                 'Einzugsgebiet',
                                 'Pot. gesparte Personenminuten',
                                 'Pot. addressierte Pendler'
                                 ])
        dl_ga.set_index(['Generation', 'Platzierung', 'Cluster'], inplace = True)
        csv = dl_ga.to_csv(float_format='%.4f').encode('utf-8')
        st.download_button("CSV-Download",csv,
                           "Ergebnis_GeneticAlgorithm.csv","text/csv",
                           key='download-ga-csv')
                    
else:
    st.markdown(f"**Diese Seite steht erst zur Verfügung,\
        wenn die Eingaben auf der Startseite getätigt wurden.**")
