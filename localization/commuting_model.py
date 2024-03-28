import os
import pickle
import pandas as pd
import numpy as np
import requests
import geopandas as gpd
from scipy.stats import beta
from scipy.special import expit
from functools import total_ordering
from tqdm import tqdm



# This code defines functions and classes for assessing potential savings through the provision of coworking spaces in different municipalities, considering commuting distances and probabilities of coworking space utilization. It uses logistic regression and beta distribution in the `llcw` function to estimate the likelihood of individuals using coworking spaces based on distances. The code also includes a `Municipality` class to represent municipalities, functions for querying commuter data and distances between municipalities, and utilizes Pickle for storing and loading commuting and distance data.



ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))
# is /home/<name>/co2work
        
def llcw(dist_cowork, dist_wpl):
    """calculates the likelihood to use the coworking space
    Arguments:
        dist_cowork : the distance to the coworking space in minutes
        dist_wpl : the distance to the workplace in minutes

    Returns:
        res : a double value between 0 and 1. Interpret as probability that coworking is used.
    """
    
    coeffs = [2.42853131, -8.19792602]
    phi = 3.9282610641028697
    X = np.stack((np.ones_like(dist_wpl), 1/np.log(dist_wpl)), axis = -1)
    mu_ = expit(np.dot(X, coeffs))
    a_ = mu_ * phi
    b_ = phi - a_
    ratio_ = (dist_wpl - dist_cowork)/dist_wpl
    param_stack = np.stack((a_, b_, ratio_), axis = -1)
    if param_stack.ndim == 1:
        param_stack = param_stack[np.newaxis,:]
    res = [beta(a, b).cdf(ratio)
            for a, b, ratio in param_stack]
    
    res = np.array(res)
    
    return res
    # res = dist_cowork < dist_wpl
    # return res

def spcw(dist_cowork, dist_wpl, metric= np.abs):
    """calculates the savings per coworker
    Arguments:
        dist_cowork : the distance to the coworking space
        dist_wpl : the distance to the workplace
        metric: the used metric. default is absolute. for squared distances use: np.square 

    Returns:
        spcw : the saving pro coworker if coworking space instead of working place is used.
    """
    res = metric(dist_cowork - dist_wpl)
    return res

def assess_savings(mun0, area):
    """calculate the savings possible by offering a coworking space in a certain municipality if it is the only coworking space in that area

    Arguments:
        mun0 : the municipality in question (AGS)
        area : list of all municipalities to which the target value refers.

    Returns:
        value : a double value. Bigger is better
    """
    # assert isinstance(mun0, Municipality), f"{mun0} not an municipality, but {type(mun0)}"
    assert area != [], f"Empty area given: {mun0} und {area}"
    
    llcw_ = [llcw(np.ones(len(res.commutes_to)) * get_dist(res, mun0),
                       np.array([get_dist(res, wpl) for wpl in res.commutes_to]))
             for res in area]
    comm_res_wpl_ = [np.array([get_commuters(res, wpl) for wpl in res.commutes_to])
                     for res in area]
    spcw_ = [spcw(np.ones(len(res.commutes_to)) * get_dist(res, mun0),
                       np.array([get_dist(res, wpl) for wpl in res.commutes_to]))
             for res in area]
    
    # calculate exact pairs res, wpl, cws
    commuters = [x*y for x,y in zip(llcw_, comm_res_wpl_)]
    savings = [x*y for x,y in zip(spcw_, commuters)]
    
    # aggregate over wpl to res, cws
    commuters = np.array([np.sum(x) for x in commuters])
    savings = np.array([np.sum(x) for x in savings])
    
    # assert X.shape[0] == 3, f"Somethings wrong: Has run assess_savings with {mun0} on area {area} lead to X = {X}"       
    # if X.shape[0] == 3: # everything is normal; proceed
    # try:
    #     dist_res_mun0, dist_res_wpl, comm_res_wpl = X 
    #     commuters = llcw(dist_res_mun0, dist_res_wpl) * comm_res_wpl      
    #     savings = spcw(dist_res_mun0, dist_res_wpl) * commuters
    # except :
    #     savings = [0 for res in area]
    #     commuters = [0 for res in area]
    
    return savings, commuters

def ags(mun_list):
    return [mun.ags for mun in mun_list]    

@total_ordering
class Municipality:
    __mundict = dict() # dictionary of all instances: ags -> municipality
    __munset = set() # set of all instances: municipality
    
    ags = property(lambda self : self.__ags) # str -> unique ID
    name = property(lambda self : self.__name) # str -> Klartext Name
    coord = property(lambda self : self.__coord) # (lat, lon) tuple -> Siedlungsschwerpunkt
    commutes_to = property(lambda self : self.__commutes_to) # commuting destinations
    
    def __init__(self, ags, name, coord):
        self.__ags = ags
        self.__name = f"{name.split(',')[0].strip()} ({name.split(',')[1].strip()})" if ',' in name else name
        self.__coord = coord
        self.__mundict[ags] = self
        self.__munset.add(self)
        pass

    def _set_commutes_to(self):
        try:
            self.__commutes_to = Municipality.get(get_commuters.image(self.ags))
        except KeyError:
            self.__commutes_to = []
    
    def __eq__(self, other):
        if type(other) == str:
            eq = self.ags == other
        else:
            eq = self.ags == other.ags
        return eq

    def __lt__(self, other):
        if type(other) == str:
            lt = self.ags < other
        else:
            lt = self.ags < other.ags
        return lt
    
    def __hash__(self):
        return hash(self.ags)        
    
    @classmethod
    def read_csv(cls, file):
        df = pd.read_csv(file, dtype={'AGS': str})
        muns = {cls(e.AGS, e.Name, (e.Latitude, e.Longitude)) for e in df.itertuples()}
        [mun._set_commutes_to() for mun in muns]   
        return muns
    
    @classmethod
    def get(cls,ags_or_region):
        try:
            result = cls.__mundict[ags_or_region]
            
        except TypeError:            
            def get(ags):
                try:
                    mun = cls.__mundict[ags]
                except:
                    mun = False
                return mun
            result = [get(ags) for ags in ags_or_region if get(ags)]
                        
        return result
    
    @classmethod
    def get_munset(cls):     
        return cls.__munset
    
    @classmethod
    def get_mundict(cls):     
        return cls.__mundict
    
    def __repr__(self) -> str:
        return f"{self.name}"
    
    def part_of(self, region):
        return self.ags.startswith(region)
    
    @classmethod
    def dissolve(cls, *args):
        def flatten(lst):
            res = []
            for x in lst:
                if isinstance(x, (list, tuple, set)):
                    res.extend(flatten(x))
                else:
                    assert isinstance(x, str), f"cannot interpret input {x} of type {type(x)}"
                    res.append(x)                    
            return res  
        region = tuple(flatten(args))
        return [mun for mun in cls.__munset if mun.part_of(region)]
    
    def get_dist(self, destination, disttype = 'duration'):
        return get_dist(self, destination, disttype)
    
    def get_commuters(self, destination):
        return get_commuters(self, destination)
    
def get_commuters(origin, destination):
    """looks up the number of commuters between two municipalities.

    Args:
        origin (Municipality): The AGS (LAU_ID) of a german municipality
        destination (Municipality): The AGS (LAU_ID) of a german municipality

    Returns:
        int: The number of commuters from origin to destination
    """
    
    # assert that origin and destination are ags of german municipalities
    
    try:
        res = get_commuters.__commuter_dict[origin.ags][destination.ags]  
    except:
        res = False # return False if no commuter number is available      
    
    return res

def get_dist(origin, destination, disttype = 'duration'):
    """looks up the linear distance between two municipalities.
    If no look-up is available, distance is calculated and stored.

    Args:
        origin (municipality): The AGS (LAU_ID) of a german municipality
        destination (municipality): The AGS (LAU_ID) of a german municipality
        disttype (str): implemented is 'duration' (default) and 'distance'

    Returns:
        np.float: The linear distance between origin and destination in kilometers
    """
    
    #symmetric distances
    #order origin and destination, such that the smaller ID is first
    if origin.ags > destination.ags:
        origin, destination = destination, origin
        
    try: 
        #look-up in cache
        res = get_dist._dist_cache[origin.ags][destination.ags][disttype]
        
    except:
        
        #get coordinates
        orig_coord = origin.coord  # lat, lon tuple
        dest_coord = destination.coord
        
        # Abfrage der Distanzen auf der FZI OSRM Instanz
        # Ports:
        # 5000: Fußgänger
        # 5001: Auto
        # 5002: Fahrrad
        url = "http://ipe-lieferbotnet.fzi.de:5001/route/v1/driving/{},{};{},{}"
        request = url.format(orig_coord[1], orig_coord[0],
                                dest_coord[1], dest_coord[0])
        response_json = requests.get(request).json()
        distance = response_json['routes'][0]['distance']/1000
        duration = response_json['routes'][0]['duration']/60                        
        
        # save in local cache
        try:
            get_dist._dist_cache[origin.ags][destination.ags] = {'duration' : duration,
                                                'distance' : distance}
        except:
            get_dist._dist_cache[origin.ags] = {destination.ags : {'duration' : duration,
                                                  'distance' : distance}}
        
        # update saved cache
        get_dist._new_cached += 1
        if get_dist._new_cached > 999:
            """Saves the cached distances on the hard drive for future loads"""
            with open(os.path.dirname(__file__) + '/distances.pickle', 'wb') as f:
                    pickle.dump(get_dist._dist_cache, f, protocol=pickle.HIGHEST_PROTOCOL)
            get_dist._new_cached = 0
            
        # look up in cache
        res = get_dist._dist_cache[origin.ags][destination.ags][disttype]
            
    return res

def delete_dist():
    """Deletes the cached distances on hard drive and in workspace"""
    try:
        os.remove(os.path.dirname(__file__) + '/distances.pickle')
    except:
        print("no cache")
    finally:
        # reset work memory
        get_dist._dist_cache = {}
        get_dist._new_cached = 0
    pass

  
# load commuter data
with open(os.path.dirname(__file__) + '/commuters.pickle', 'rb') as f:
    get_commuters.__commuter_dict = pickle.load(f)
    
get_commuters.image = lambda ags: get_commuters.__commuter_dict[ags].keys() 

# loading municipality data
with open(ROOT_DIR + '/data/processed/Gemeinden/AlleGemeinden.csv') as f:
    Municipality.read_csv(f)
    
# load cached distances
try:
    with open(os.path.dirname(__file__) + '/distances.pickle', 'rb') as f:
        get_dist._dist_cache = pickle.load(f)
        get_dist._new_cached = 0
except:
    get_dist._dist_cache = {}
    get_dist._new_cached = 0 
