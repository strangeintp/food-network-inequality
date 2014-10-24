""" forager.py
an agent for use with the foraging-gift-giving ABM

ASSUMPTIONS:
Foragers are monogamous
"""

import random as rnd
import hhagent as HH
import utility as U
import world as W

"""
enums
"""

# life stages
INFANT = 0
JUVENILE = 1
ADULT = 2
SENIOR = 3

"""
parameters
"""
# the age until which an agent is helpless
AGE_OF_JUVENILE = 5
# the age at which an agent becomes self-sufficient
AGE_OF_ADULT = 15
# 
AGE_OF_SENIOR = 45
OLDEST = 75

STARVATION_THRESHOLD = 0.1

avg_foraging_expertise = 1.3
def setAvgForagingExpertise(val = avg_foraging_expertise):
    global avg_foraging_expertise
    val = float(val)
    avg_foraging_expertise = val
    return val

stddev_foraging_expertise = 0.1
def setSdvForagingExpertise(val = stddev_foraging_expertise):
    global stddev_foraging_expertise
    val = float(val)
    stddev_foraging_expertise = val
    return val

def homogeneous():
    return stddev_foraging_expertise==0


DEBUG=True

def debug(s):
    if DEBUG:
        print(s)


world = None
        
class Ancestry(object):
    
    def __init__(self, person, generations=2):
        self.person = person #the actual person object represented by this node
        self.ancestors = [None, None]
        self.past_length = generations  # how far back the person tracks ancestors
        parents = person.parents
        if len(parents)==2:
            self.ancestors[0] = [parents[0].ID, Ancestry.Generate(parents[0].ancestry.ancestors, generations-1)]
            self.ancestors[1] = [parents[1].ID, Ancestry.Generate(parents[1].ancestry.ancestors, generations-1)]
    
    @staticmethod
    def Generate(parent_ancestors, generations):
        #recursively add parent ancestries until generation tracking variable equals 0
        ancestors = [None, None]
        if generations>0:
            if ancestors[0] != None:
                ancestors[0] = [parent_ancestors[0][0], Ancestry.Generate(parent_ancestors[0][1], generations-1)]
            if ancestors[1] != None:
                ancestors[1] = [parent_ancestors[1][0], Ancestry.Generate(parent_ancestors[1][1], generations-1)]
        return ancestors
    
    def getAncestors(self, ancestors=None, generations=-1):
        if generations==-1:
            generations = self.past_length
        if ancestors==None:
            ancestors = self.ancestors
        ancestor_set = set()
        if generations<=0:
            return ancestor_set
        if ancestors[0] != None:
            ancestor_set = ancestor_set.union(set([ancestors[0][0]]))
            ancestor_set = ancestor_set.union(self.getAncestors(ancestors[0][1], generations-1))
        if ancestors[1] != None:
            ancestor_set = ancestor_set.union(set([ancestors[1][0]]))
            ancestor_set = ancestor_set.union(self.getAncestors(ancestors[1][1], generations-1))
        return ancestor_set
              
    def isKin(self, other):
        my_ancestors = self.getAncestors() | set([self.person.ID])
        their_ancestors = other.getAncestors() | set([other.person.ID])
        return my_ancestors & their_ancestors

class Forager(object):
    
    next_ID = 0
    death_count = 0
    
    @staticmethod
    def reset():
        Forager.next_ID = 0
        Forager.death_count = 0
    
    def __init__(self, age=0, parents=[], kinship_span=2):
        self.ID = Forager.next_ID
        Forager.next_ID += 1
        self.household = None
        self.lineage = None
        self.mate = None
        self.innate_foraging_expertise = avg_foraging_expertise
        
        self.kinship_span = kinship_span
        self.parents = parents
        for parent in parents:
            self.lineage = parent.household.lineage
            self.kinship_span = parent.kinship_span
        self.ancestry = Ancestry(self, generations=self.kinship_span)
        
        if age==-1:
            self.age = rnd.randrange(AGE_OF_ADULT,AGE_OF_SENIOR)
        else:
            self.age = age
        self.max_age = OLDEST
        self.alive = True
        self.food_need = self.getBaseFoodNeed()
        self.amount_fed = self.food_need
        self.setExpertise()
        
    
    def setExpertise(self):
        avg = avg_foraging_expertise
        stddev = stddev_foraging_expertise
        if stddev==0:
            exp = avg
        else:
            #clamp between 6-sigma extremes
            lb = -6*stddev
            ub = 6*stddev
            # have to multiply by 10 first because small values break random.gauss()
            birth_factor = U.randomBoundedNormal(0, stddev*10, lb*10, ub*10)
            birth_factor = 1 + birth_factor/10 # recorrect by factor of 10
            if len(self.parents) == 2:
                w1 = rnd.random()*0.5 + 0.25
                w2 = 1 - w1
                exp = w1*self.parents[0].foragingExpertise() + w2*self.parents[1].foragingExpertise()
            else:
                exp = avg
                
            exp *= birth_factor
            # clamp between [0, 2*avg]
            if exp<0:
                exp=0
            if exp>2*avg:
                exp=2*avg
                    
        self.innate_foraging_expertise = exp
    
    def setKinshipSpan(self, kinship_span=2):
        span = kinship_span
        if len(self.parents) == 2:
            if rnd.random() < 0.5:
                span = self.parents[0].kinship_span
            else:
                span = self.parents[1].kinship_span
        
        self.kinship_span = span
    
    def step(self):
        self.age += 1
        
        if not self.hasDied():
            if self.age==AGE_OF_ADULT:
                world.spawnHouseholdFrom(self)
            if self.isBachelor():
                self.findAMate()
        
        self.food_need = self.getBaseFoodNeed() + self.foodRequired()
        self.amount_fed = 0
            
    def getBaseFoodNeed(self):
        base_need = 0
        if self.age < AGE_OF_ADULT:
            base_need = max([1/AGE_OF_ADULT, self.age/AGE_OF_ADULT])
        else:
            base_need = 1.0
        return base_need
    
    def eat(self, amount):
        self.amount_fed += amount
        
    def move(self, move_cost):
        self.amount_fed -= move_cost
        
    def getHealth(self):
        return self.amount_fed/self.food_need
    
    def foodRequired(self):
        return self.food_need - self.amount_fed         
    
    def isBachelor(self):
        return self.age>=AGE_OF_ADULT and self.mate==None
    
    def marry(self, mate):       
#         if not self.isParentOfHousehold():  # self keeps current household if a parent
#             #otherwise, moves out and spawns a new house
#             world.spawnHouseholdFrom(self)
        if mate.isParentOfHousehold():  # mate moves to new household with family
            self.household.combineWith(mate.household)
        self.mate = mate
        mate.mate = self
        self.household.addParent(mate)
    
    def joinHousehold(self, hh):
        old_hh = self.household
        if old_hh != None:
            old_hh.removeMember(self)
        self.household=hh
        if self.lineage==None:
            lineage = hh.lineage
            
    def isParentOfHousehold(self):
        if self.household != None:
            if self.household.parents.count(self) > 0:
                return True
            else:
                return False
        else:
            return False
             
    def findAMate(self):
        neighbors = world.getNeighborhoodOf(self.household)
        bachelors = []
        for neighbor in neighbors:
            bachelors.extend(neighbor.getBachelors())
        rnd.shuffle(bachelors)
        for bachelor in bachelors:
            if not self.findKinshipWith(bachelor):
                self.marry(bachelor)
                break

    def findKinshipWith(self, other):
        return self.ancestry.isKin(other.ancestry)
    
    def traceAncestry(self):
        return self.ancestry.getAncestors()
    
    def hasDied(self):
        if self.age==self.max_age or self.getHealth() < 0:
            Forager.death_count += 1
            self.alive = False    
        return not self.alive 
    
    def foragingExpertise(self):
        expertise = self.innate_foraging_expertise
        if self.age < AGE_OF_JUVENILE :
            return 0
        elif self.age < AGE_OF_ADULT:
            return expertise*(self.age-AGE_OF_JUVENILE)/AGE_OF_JUVENILE
        else:
            return expertise
    
    def isAdult(self):
        return self.age >= AGE_OF_ADULT
    
    def isSenior(self):
        return self.age > AGE_OF_SENIOR
    
    def getLifeStage(self):
        if self.age > AGE_OF_SENIOR:
            return SENIOR
        elif self.age > AGE_OF_ADULT:
            return ADULT
        elif self.age > AGE_OF_JUVENILE:
            return JUVENILE
        else :
            return INFANT


"""
MAIN
"""
if __name__ == '__main__':
    import foraging_simGUI as sim
    sim.run()