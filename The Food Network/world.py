
import random as rnd
import hhagent as HH
import forager as F
import landscape as L
import utility as U
import math

DEFAULT_SIZE = 1

starting_agents = 256
def setStartingPopulation(val=starting_agents):
    global starting_agents
    starting_agents = int(val)
    return starting_agents

min_resource = 2
def setMinResource(val=min_resource):
    global min_resource
    min_resource = float(val)
    return min_resource

max_resource = 8
def setMaxResource(val=max_resource):
    global max_resource
    max_resource = float(val)
    return max_resource

regrowth_steps = 8
def setRegrowthSteps(val=regrowth_steps):
    global regrowth_steps
    val = float(val)
    regrowth_steps = val
    return regrowth_steps

max_founder_kin_span = 6
min_founder_kin_span = 2
def setMinKinSpan(val=min_founder_kin_span):
    global min_founder_kin_span
    val = float(val)
    min_founder_kin_span = val
    return val

def setMaxKinSpan(val=max_founder_kin_span):
    global max_founder_kin_span
    val = float(val)
    max_founder_kin_span = val
    return val

def setKinSpan(val=max_founder_kin_span):
    global max_founder_kin_span, min_founder_kin_span
    val = float(val)
    max_founder_kin_span = val
    min_founder_kin_span = max_founder_kin_span
    return val

resource_zero = 0.1  # landscape resources can't actually go to zero or it won't regrow

DEBUG=True

def debug(s):
    if DEBUG:
        print(s)

addlocs = lambda a,b: tuple((ax+bx)%L.width for ax,bx in zip(a,b))

class World(object):
       
    def __init__(self, size=DEFAULT_SIZE, numagents=starting_agents, landscape = L.Landscape()):
        HH.HHAgent.reset()
        F.Forager.reset()
        HH.world = self
        F.world = self
        
        self.foraging_resources = landscape.normalizeTo(max_resource, min_resource)
        self.max_foraging_resources = self.foraging_resources.copy()
        
        self.hh_locations = {}
        self.avg_hh_x = []
        self.avh_hh_y = []
        self.houses_by_loc = {}
        self.regrowth_rate = {}
        self.lineages = [i for i in range(numagents)]
        self.kinship_spans = []
        self.hh_food_stored = []
        self.pop_expertise = []
        self.max_prestige = []
        for x in range(L.width):
            for y in range(L.width):
                self.houses_by_loc[x,y] = [] 
                resource = self.max_foraging_resources[x,y] 
                self.regrowth_rate[x,y] = math.exp((math.log(resource) - math.log(resource_zero))/regrowth_steps)
        
        self.households = [HH.HHAgent() for i in range(numagents)]
        avg_x = 0
        avg_y = 0
        span_interval = (max_founder_kin_span - min_founder_kin_span)/numagents
        for hh in self.households:
            location = (rnd.randrange(L.width),rnd.randrange(L.width))
            x, y = location
            avg_x += x
            avg_y += y
            self.hh_locations[hh] = location
            self.houses_by_loc[location].append(hh)
            lineage_kinship_span = min_founder_kin_span + span_interval*hh.lineage
            founder = F.Forager(-1, kinship_span=lineage_kinship_span) # create a new forager with random adult age
            hh.addParent(founder)
            self.kinship_spans.append(lineage_kinship_span)
            self.pop_expertise.append(founder.innate_foraging_expertise)
            spouse = F.Forager(founder.age, kinship_span=lineage_kinship_span)
            founder.marry(spouse)
            self.kinship_spans.append(lineage_kinship_span)
            self.pop_expertise.append(spouse.innate_foraging_expertise)
            self.hh_food_stored.append(0)
        
        # metrics initializations
        avg_x /= numagents
        avg_y /= numagents    
        self.population = sum([hh.size() for hh in self.households])
        self.populations = [self.population]
        self.avg_pop = [self.population]
        self.avg_pop_100 = [self.population]
        self.avg_hh_size = [2]
        self.avg_hh_age = [0]
        self.tot_hh_age = 0
        self.dead_houses = 1
        self.food_shared = [0]
        self.food_shared_total = 0
        self.food_shared_totals = [0]
        self.com_sharing = []  #communal sharing
        self.brn_sharing = []
        self.grn_sharing = []
        self.ages_at_death = []
        self.avg_ages = []  # track average ages at death at each tick for plotting
        self.adult_ages_at_death = []
        self.avg_adult_ages = [] # track average adult ages at death at each tick for plotting
        self.hh_prestige = []
        self.median_storage = [0]
        self.max_hoover = []
        self.avg_hoover = []
        self.avg_food_stored = []
            
    def spawnHouseholdFrom(self, forager):
        location = self.hh_locations[forager.household]
        new_hh = HH.HHAgent(lineage=forager.lineage)
        new_hh.addParent(forager)
        self.households.append(new_hh)
        self.hh_locations[new_hh] = location
        self.houses_by_loc[location].append(new_hh)
    
    def bestLocationAt(self, pos):
        max_resources = 0
        maxloc = (0,0)
        a_set = [i for i in range(-1,2)]
        b_set = [i for i in range(-1,2)]
        rnd.shuffle(a_set)
        rnd.shuffle(b_set)
        locs = [addlocs(pos,(a,b)) for a in a_set for b in b_set]
        for loc in locs:
            resources = self.foraging_resources[loc]
            if max_resources < resources:
                max_resources = resources
                maxloc = loc
        
        return (maxloc, max_resources)
    
    def step(self):
        emptyhouses = []
        self.food_shared_step = 0
        
        #activation order
        if F.homogeneous():  # completely random activation order if homogeneous foraging abilities
            rnd.shuffle(self.households)
        else:   # activate based on foraging ability with some randomness
            activation_order = lambda hh : hh.foragingAbility()*U.GenBoundedRandomNormal(1, 0.2, 0.5, 1.5)
            self.households = sorted(self.households, key=lambda hh: activation_order(hh))
        avg_x=0
        avg_y=0
        self.population = 0
        self.kinship_spans = []
        self.hh_food_stored = []
        self.pop_expertise = []
        self.hh_prestige = []
        
        self.brn_sharing.append(0)
        self.grn_sharing.append(0)
        self.com_sharing.append(0)
        for hh in self.households:
            hh.step()
            
            if hh.hasDied():
                emptyhouses.append(hh)
                self.tot_hh_age += hh.age
                self.dead_houses += 1
            else:
                self.population += hh.size()
                x, y = self.hh_locations[hh]
                avg_x += x
                avg_y += y
                for member in hh.members():
                    self.kinship_spans.append(member.kinship_span)
                    self.pop_expertise.append(member.innate_foraging_expertise)
                self.hh_prestige.append(hh.prestige())
                self.hh_food_stored.append(hh.food_storage)
        
        for hh in emptyhouses:
            self.removeHousehold(hh)
        
        self.regrowth()
        
        #metrics
        self.avg_hh_age.append(self.tot_hh_age/self.dead_houses)
#         self.avg_hh_age.append(self.tot_hh_age/len(self.dead_houses))
        if len(self.households)>0:
            self.avg_hh_size.append(self.population/len(self.households))
        else :
            self.avg_hh_size.append(0)
        self.food_shared.append(self.food_shared_step)
        self.food_shared_total += self.food_shared_step
        self.food_shared_totals.append(self.food_shared_total)
        
        self.populations.append(self.population)
        self.avg_pop.append(sum(self.populations)/len(self.populations))
        if len(self.populations) < 100:
            self.avg_pop_100.append(sum(self.populations)/len(self.populations))
        else:
            self.avg_pop_100.append(sum(self.populations[-100:])/100)
            
        self.avg_ages.append(U.mean(self.ages_at_death))
        self.avg_adult_ages.append(U.mean(self.adult_ages_at_death))
        self.computeWealthMetrics()
        
    def computeWealthMetrics(self):
        self.median_storage.append(U.median(self.hh_food_stored))
        self.avg_food_stored.append(U.mean(self.hh_food_stored))
        
    def reportFoodSharing(self, amount):
        self.food_shared_step += amount
    
    def reportBRNSharing(self, amount):
        self.brn_sharing[-1] += amount
    
    def reportGRNSharing(self, amount):
        self.grn_sharing[-1] += amount
        
    def reportCOMSharing(self, amount):
        self.com_sharing[-1] += amount
    
    def reportADeath(self, forager):
        self.ages_at_death.append(forager.age)
        if forager.age >= F.AGE_OF_ADULT:
            self.adult_ages_at_death.append(forager.age)
    
    def regrowth(self):
        hoovers = []
        for x in range(L.width):
            for y in range(L.width):
                if self.foraging_resources[(x,y)] <= 0 :
                    # landscape resources can't actually go to zero or it won't regrow
                    self.foraging_resources[(x,y)] = resource_zero 
                self.foraging_resources[(x,y)] *= self.regrowth_rate[x,y]
                if self.foraging_resources[(x,y)] > self.max_foraging_resources[(x,y)]:
                    self.foraging_resources[(x,y)] = self.max_foraging_resources[(x,y)]
                #compute the local hoover index
                residents = self.getNeighborsAround2((x,y), radius=1)
                stored_amounts = []
                for resident in residents:
                    stored_amounts.append(resident.food_storage)
                local_hoover = U.HooverIndex(stored_amounts)
                hoovers.append(local_hoover)
        self.max_hoover.append(max(hoovers))
        self.avg_hoover.append(U.mean(hoovers))
                
            
    def forageResources(self, hh, amount_to_gather):
        location = self.hh_locations[hh]
        if self.foraging_resources[location]<=0:
            gathered = 0
        elif amount_to_gather > self.foraging_resources[location]:
            gathered = self.foraging_resources[location]
        else:
            gathered = amount_to_gather
        self.foraging_resources[location] -= gathered
        
        return gathered
    
    def getNeighborhoodOf(self, hh, radius=1):
        p0 = self.locationOf(hh)
        neighborhood = []
        r_squared = radius*radius
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                if (dx**2 + dy**2) <= r_squared:
                    neighborhood.extend(self.houses_by_loc[addlocs(p0, (dx,dy))])
        neighborhood.remove(hh)
        rnd.shuffle(neighborhood)
        
        return neighborhood
    
    def getNeighborsAround(self, p0, radius=1):
        neighborhood = self.getNeighborsAround2(p0, radius)
        rnd.shuffle(neighborhood)
        
        return neighborhood
    
    def getNeighborsAround2(self, p0, radius=1):
        neighborhood = []
        r_squared = radius*radius
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                if (dx**2 + dy**2) <= r_squared:
                    neighborhood.extend(self.houses_by_loc[addlocs(p0, (dx,dy))])
        
        return neighborhood
    
    def moveHousehold(self, hh, p):
        location = addlocs(self.hh_locations[hh], p)
        old = self.hh_locations[hh]
        self.hh_locations[hh] = location
        self.houses_by_loc[old].remove(hh)
        self.houses_by_loc[location].append(hh)
    
    def moveHouseholdTo(self, hh, p):
        old = self.hh_locations[hh]
        self.houses_by_loc[old].remove(hh)
        self.hh_locations[hh] = p
        try:
            self.houses_by_loc[p].append(hh)
        except:
            pass
        
    def removeHousehold(self, hh):
        try :
            self.households.remove(hh)
            loc = self.hh_locations[hh]
            del self.hh_locations[hh]
            self.houses_by_loc[loc].remove(hh)
        except:
            pass
        
    def locationOf(self, hh):
        try:
            loc = self.hh_locations[hh]
        except :
            loc = (0,0)
        return loc
    
    def resourcesAt(self, loc):
        return self.foraging_resources[loc]
    
"""
MAIN
"""
if __name__ == '__main__':
    import foraging_simGUI as sim
    sim.run()