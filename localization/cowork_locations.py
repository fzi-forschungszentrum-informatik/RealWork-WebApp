import numpy as np
import pandas as pd
from tqdm import tqdm
from functools import lru_cache, total_ordering
import concurrent
import copy
import sys
sys.path.append('.../co2work/code/localization')
import commuting_model as como


# This code gives solutions to a coworking space optimization problem within a specified region. It does so by cinluding methods for mutation, combination, and updating based on specific criteria. The code further implements a genetic algorithm and a kLocs algorithm for optimizing coworking space locations. Additionally, there is a function for generating heatmaps to visualize potential improvements in coworking space locations compared to a reference solution.


@total_ordering
class Solution:    
    
    def __init__(self, region, locs = False, **kwargs) -> None:
        """generates a Solution in a region, either with given locations
        for coworoking spaces or with randomly assigned locations from the region.
        

        Args:
            region (lst of AGS-Prefix or lst of como.Municipality): region in which coworking spaces shall be optimized
            locs (lst of AGS, optional): Given Locations. Defaults to False -> Randomly generating.
            n_cws (int, mandatory if no locs are given): number of randomly generated locations.
            fixed_cws (lst of AGS, optional): fixed locations for coworking spaces
           
        """
        # set region
        if all(isinstance(el, como.Municipality) for el in region):
            self.__region = region
        else:
            self.__region = como.Municipality.dissolve(tuple(region))
        
        if 'fixed_cws' in kwargs:
            fixed_cws = kwargs['fixed_cws']
            self.__n_fixed = len(fixed_cws)
        else:
            fixed_cws = []
            self.__n_fixed = 0
            
        if not locs:
            assert 'n_cws' in kwargs, f"If no locs are given, one has to provide the number of coworking spaces to set (n_cws)"
            self.__n_cws = kwargs['n_cws']
            assert self.n_cws > self.n_fixed, f"More fixed cws than cws to be set. Ensure n_cws > len(fixed_cws)"
            candidates = [mun for mun in self.region if mun not in fixed_cws]
            locs = [*fixed_cws,
                    *np.random.choice(candidates,
                                      size=self.n_cws-self.n_fixed,
                                      replace=False)]
        else:
            self.__n_cws = len(locs)
            assert(all([e in locs for e in fixed_cws])), f"locs must contain every fixed_cws"
            assert(all([mun in self.region for mun in locs])), f"locs must be in self.region"
                      
        self.__locs = locs
        self.update()
    
    def __eq__(self, other):
        return self.total_saving == other.total_saving

    def __lt__(self, other):
        return self.total_saving < other.total_saving
    
    def __hash__(self):
        return hash(set(self.locs))      
        
    @property
    def locs(self):
        return self.__locs
    
    @locs.setter
    def locs(self, val):                       
        self.__locs = val
        self.update()
        
    @property
    def region(self):
        return self.__region
    
    @region.setter
    def region(self, val):
        if all(isinstance(el, como.Municipality) for el in val):
            self.__region = val
        else:
            self.__region = como.Municipality.dissolve(tuple(val))
        self.update()  
    
    @property
    def fixed_cws(self):
        return self.locs[0:self.__n_fixed]
    
    @property
    def variable_cws(self):
        return self.locs[self.__n_fixed:]
    
    @property
    def n_cws(self):
        return self.__n_cws   
    
    @property
    def n_fixed(self):
        return self.__n_fixed   
    
    @property
    def areas(self):
        return self.__areas        

    @property
    def savings(self):
        """ returns savings from mun in area to loc as list of arrays"""
        return self.__savings

    @property
    def area_savings(self):
        """ returns savings aggregated by areas as list """
        return self.__area_savings
          
    @property
    def total_saving(self):
        """ returns total saving of solution as number """
        return self.__total_saving     
    
    @property
    def commuters(self):
        """ returns commuters from mun in area to loc as list of arrays"""
        return self.__commuters

    @property
    def area_commuters(self):
        """ returns commuters aggregated by areas as list"""
        return self.__area_commuters
          
    @property
    def total_commuters(self):
        """ returns total commuters of solution as number """
        return self.__total_commuters
    
    def _set_savings_commuters(self, savings, commuters):
        self.__savings = [saving for saving in savings]
        self.__commuters = [commuter for commuter in commuters]        
        self.__area_savings = [np.sum(area_savings) for area_savings in self.savings]  
        self.__area_commuters = [np.sum(area_commuters) for area_commuters in self.commuters]      
        self.__total_saving = np.sum(self.area_savings) 
        self.__total_commuters = np.sum(self.area_commuters)
        pass   
        
    def update(self):
        """updates areas and savings of a solution."""    
        # calculating areas        
        nearest_loc = {mun: self.locs[np.argmin([como.get_dist(mun, loc) for loc in self.locs])] for mun in self.region}
        new_areas = [[mun for mun in self.region if nearest_loc[mun] == loc] for loc in self.locs]        
        self.__areas = new_areas
        
        sav_comm = [como.assess_savings(locs, new_areas[i])
                          for i, locs in enumerate(self.locs)] 
        self.__savings = [saving for saving, _ in sav_comm]
        self.__commuters = [commuter for _, commuter in sav_comm]        
        self.__area_savings = [np.sum(area_savings) for area_savings in self.savings]  
        self.__area_commuters = [np.sum(area_commuters) for area_commuters in self.commuters]      
        self.__total_saving = np.sum(self.area_savings) 
        self.__total_commuters = np.sum(self.area_commuters)
        pass
    
    def __repr__(self):
        return f"{self.locs}"
    
    def mutate(self, p_mut):
        """mutates every non-fixed cws location with probability p_mut

        Args:
            p_mut (float): probability that a non-fixed cws in locs is changed
        """
        p_stay = 1 - p_mut
        
        exclude = []
        def mut(locs, pos):
            mun = locs[pos]
            candidates = np.intersect1d(mun.commutes_to, self.region)
            candidates = [cand for cand in candidates \
                          if cand not in locs
                          and cand not in exclude]
            weights = [mun.get_commuters(wpl) for wpl in candidates]
            candidates = [mun, *candidates] # candidates at least one long (original)
            weights = [p_stay*np.sum(weights)+.1, *weights] # original location gets p_mut of weight + epsilon (.1) to ensure it is picked if no 
            res = np.random.choice(candidates,
                                   p = weights/np.sum(weights))
            exclude.append(res) # ensure that not two muns mutate to same mun         
            return res
            
        mut_alt = [mut(self.locs, pos) for pos in np.arange(self.n_fixed,self.n_cws)]
        
            
        self.locs = [*self.fixed_cws, *mut_alt]
        return self
    
    def combine(self, other, agg_func = np.union1d, agg_n_cws = max):
        """combines two Solutions into a new one.

        Args:
            other (solution): another solution
            agg_func (method, optional): how region is aggregated. Defaults to np.union1d.
            agg_n_cws (method, optional): how n_cws is aggregated. Defaults to max.

        Returns:
            Solution: a new solution based on seld and other
        """
        region = agg_func(self.region, other.region)
        fixed_cws = np.union1d(self.fixed_cws, other.fixed_cws)
        candidates = np.intersect1d(np.union1d(self.locs, other.locs), region)
        candidates = [cand for cand in candidates \
            if cand not in fixed_cws]
        n_cws = agg_n_cws(self.n_cws, other.n_cws)
        locs = [*fixed_cws,
                *np.random.choice(candidates,
                                  size = n_cws - len(fixed_cws),
                                  replace = False)]
        return Solution(region = region,
                        fixed_cws = fixed_cws,
                        locs = locs)
        
    def step(self):     
        """
        for every area, that does belong to a placed coworking space, i.e. not belongs to an existing coworking space,
        find that alternative municipality inside that label that is also a candidate and minimizes the target function       
        """
        alt_centers = [[mun for mun in self.areas[pos]]
                       for pos in np.arange(self.n_fixed,self.n_cws)]
                
        def calc_alt_saving(pos):
            alt_center_list = alt_centers[pos - self.n_fixed]
            alt_saving = [np.sum(como.assess_savings(alt_center, self.areas[pos])[0])
                          for alt_center in alt_center_list]
            alt_center = alt_center_list[np.argmax(alt_saving)]
            return alt_center
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            best_alt = list(executor.map(calc_alt_saving, np.arange(self.n_fixed, self.n_cws)))
        
        self.locs = [*self.fixed_cws, *best_alt]
        self.update()
        return self
    
    
    def check(self):
        return all([self.locs[i] in self.areas[i] for i in range(self.n_cws)])
        
def genetic_algorithm(n_pop, n_gen, p_survive, p_mut, n_best =5, **kwargs):
    """performs the genetic algorithm on a given set of solution parameters (kwargs)

    Args:
        n_pop (int): Population size 
        n_gen (int): Number of generations to calculate
        p_survive (float [0, 1]): probability of survival in each generation
        p_mut (float [0, 1]): probability of mutation in each location
        kwargs: arguments for initializing Solutions. Mandatory.
        seed (int; optional): seed for np.random
        progress (optional) : a streamlit progressbar 

    Returns:
        df: results
    """
    n_survivors = int(p_survive*n_pop)
    result_df = []
    
    if 'seed' in kwargs:
        np.random.seed(kwargs['seed'])
        
    # generation
    population = [Solution(**kwargs) for i in range(n_pop)]
    
    wo_tqdm_range = range(n_gen) if 'progress' in kwargs else tqdm(range(n_gen), desc = "Generations")
    for i in wo_tqdm_range: 
        # save best results of that generation
        best = np.unique(population)[-n_best:]
        best = [copy.copy(sol) for sol in best]
        for j in range(n_best):
            result_df.append([i, n_best-j, best[j], best[j].check()])
        
        #fitness    
        pop_fitness = [sol.total_saving for sol in population]
        
        if 'progress' in kwargs:
            kwargs['progress'].progress((i+1)/(n_gen+1),
                                        text=f"Die beste gefundene Lösung spart zusätzlich potentiell\
                                            {'{:0,.2f}'.format(max(pop_fitness)-kwargs['ref_saving'])}\
                                                Personenkilometer ein.")
        
        pop_fitness = pop_fitness - min(pop_fitness)

        # selection (fitness-proportional roulette)
        population = np.array(population) # must be array
        survivors = population[np.random.choice(n_pop,
                                               size = n_survivors,
                                               p = pop_fitness/sum(pop_fitness),
                                               replace = False)]
        

        # combination
        parents = [survivors[np.random.choice(n_survivors,
                                              size = 2, replace = False)]
                   for i in range(n_pop-n_survivors)]
        childs = [x.combine(y) for x, y in parents]
        population = [*survivors, *childs]
        assert all([sol.check() for sol in population])

        # mutation        
        [sol.mutate(p_mut) for sol in population]
        
    best = np.unique(population)[-n_best:]
    best = [copy.copy(sol) for sol in best]
    i += 1
    for j in range(n_best):
        result_df.append([i, n_best-j, best[j], best[j].check()])
    
    if 'progress' in kwargs:
        kwargs['progress'].progress(100,
                                    text=f"Die beste gefundene Lösung spart zusätzlich potentiell\
                                        {'{:0,.2f}'.format(best[n_best-1].total_saving-kwargs['ref_saving'])}\
                                            Personenkilometer ein.")
    
    result_df = pd.DataFrame(result_df,
                             columns=['Generation',
                                      'Best',
                                      'Solution',
                                      'Check'])
    result_df.set_index(['Generation', 'Best'], inplace = True)
        
    return result_df

#K-Locs Algorithm
def kLocs(**kwargs):
    """performs the kLoc algorithm

    Arguments:
        kwargs: arguments for initializing Solutions. Mandatory.
        seed (int; optional): seed for np.random

    Returns:
        result_df : a pandas dataframe that consist of the chosen municipalities to host coworking spaces including
        already existing ones; columns are
        'step' : The step in optimization. 0 is initialization
        'ID' : identifier of coworking space
        'AGS' : the AGS of coworking space i
        'Value' : the value of coworking space i regarding the assess function
        'Area' : a list of AGS belonging to that coworking space
    """
    
    # Initialization
    step = 0
    total_saving = 0
    result_ls = []
    
    if 'seed' in kwargs:
        np.random.seed(kwargs['seed'])
        
    current = Solution(**kwargs)

    # Iterationen
    while True:
        ## append results from step and continue with next iteration
        # result_ls +=  [[step, i, current.locs[i], current.savings[i], current.areas[i]] for i in current.n_cws]
        result_ls += [[step, copy.copy(current)]]
        current.step()
        
        if current.total_saving > total_saving: # check if step has improved, else break
            total_saving = current.total_saving
            step += 1            
        else:
            break

    result_df = pd.DataFrame(result_ls, columns=['Step', 'Solution'])
    result_df.set_index(['Step'], inplace = True)
    return result_df

def heatmap(region, fixed_cws, **kwargs):
    """calculates a heatmap

    Arguments:
        region : a list of AGS; the municipalities of the investigated region
        fixed_cws : a list of AGS; the municipalities in the region that already host a coworking space

    Returns:
        result_df : a pandas dataframe that consist of the chosen municipalities to host coworking spaces including
        already existing ones; columns are
        'AGS' : the ags of the municipality potentially hosting the new coworking space
        'Improvement' : the improvement of that coworking space to the status quo ante
        'Area' : a list of AGS belonging to that coworking space
    """        
    
    # n_cws = len(fixed_cws) + 1
        
    region = como.Municipality.dissolve(region)
    
    if fixed_cws:
        ref_sol =Solution(region = region, fixed_cws = fixed_cws, locs = fixed_cws)
        reference = ref_sol.total_saving
    else:
        reference = 0
        
    
    def improvement(mun):
        if mun in fixed_cws:
            sol = ref_sol
            res = 0
        else:
            sol = Solution(region = region, fixed_cws = fixed_cws, locs = [*fixed_cws, mun])
            res = sol.total_saving - reference
        return [sol, res]
    
    
    # unparallelized
    results = []
    for i, mun in enumerate(region):
        results.append([mun.ags, mun, *improvement(mun)])
        if 'progress' in kwargs:
            kwargs['progress'].progress(i/len(region),
                                        text=f"Berechnet Gemeinde {i+1} von {len(region)}")
    
              
    # result_df = pd.DataFrame(results, columns=['CWS', 'Improvement'])
    # result_df.Improvement = result_df.Improvement - reference.total_saving
    # result_df.set_index(['CWS'], inplace = True)
    return pd.DataFrame(results,
                        columns = ['LAU_ID', 'LAU', 'Solution', 'Improvement'])
