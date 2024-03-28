# RealWork Python Web App

![Data Preparation](https://hop.fzi.de/wordpress/wp-content/uploads/2022/06/KR_RealWork_Logo2021_RGB-768x309.png)


### This software was developed as part of the research project [RealWork](https://hop.fzi.de/real-work/)

## 🖥️ What does this Webapp do?
This webapp calculates the optimal location for coworking spaces in the countryside as part of the RealWork project. It takes into account potential coworking locations, mapdata and commuting data.


## 💡 What is the RealWork project?
The RealWork project is investigating how the new coworking form of work can be 
can be adapted to employees in normal employment relationships. 
Research is being conducted into the potential of coworking for 
services of general interest and the regional management of rural 
municipalities, what advantages exist and how these advantages can be 
advantages and how these advantages can be used. The aim is through increased 
reduce commuter flows from the countryside to the city. 
At the same time, there are also new needs for public transport in rural regions 
regions (optimization of the transport infrastructure, improvement of 
air quality, new design options for mobility management). 
RealWork-Spaces are also intended to specifically serve the development of rural 
centers.



## 📥 Why is it required?

RealWork-Spaces are intended to relieve employees of the financial, social and psychological costs of commuting without having to deal with the negative side effects of working from home. On the other hand, people who currently live in the city have the option of relocating to take advantage of the benefits of rural areas, such as lower housing costs and a wider range of daycare and school facilities. Employers can organize structures and resources more flexibly at their own location and realize personnel growth without having to expand their premises. Municipalities benefit above all from a revival in the area surrounding the RealWork-Spaces, which can be reflected in particular in the catering and retail sectors. Reduced vacancy rates provide new impetus for building culture and the promotion of creativity and cross-company networks. RealWork-Spaces fulfill functions comparable to innovation hubs.



# 🏁 How to start the webapp
You can start the webapp with the following steps:
1. **cd code**

2. **pipenv shell**

3. **streamlit run webapp/Home.py**




# 📊 Data Preparation for the webapp

## Instructions

### Build a "Candidate Set" by doing the two following steps:

1. **Load Your Data in Home.py**
   - Open Home.py and navigate to line 41.
   - Load your data using the following variables: "county_df" and "municipality_df".

2. **Adjust Default Selection in Home.py**
   - Modify default selections based on your own created "candidate sets" in Home.py.
   - Update variables: "selected_counties" and "existing_cws".

## Create Your Own Candidate Sets

### Municipalities Data Structure
- The format of the input file for municipalities has to include the following columns: `AGS, Name, Latitude, Longitude`
- The webapp itself works with an output binary .pickle (for the case of Germany e.g. one per federal state) file which has to be created in the data pre-processing

### Districts or Counties Data Structure
- The format of the input file for municipalities has to include the following columns: `AGS, Name`
- The webapp itself works with an output binary .pickle (for the case of Germany e.g. one per district or county (smaller decentralised value)) file which has to be created in the data pre-processing

### Commuters Data Structure
- The input for the commuters has to be in an excel file with subpages for outgoing and incoming commuters.
  - Each subpage (for outgoing and incoming commuters) structure is to be setup as follows: `Place of Living, Name of Place of Living, Place of Work, Place of Work Name, Total, Men, Women, Nationality, Foreigners, Trainees`
- Save as a binary .pickle file.


Feel free to reach out for any clarification or assistance. Happy coding!
