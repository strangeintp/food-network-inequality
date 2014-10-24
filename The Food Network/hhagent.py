import forager as F
import random as rnd
import utility as U
import landscape as L
import world as W


DEBUG=True

def debug(s):
    if DEBUG:
        print(s)

subsistence_threshold = 1
def setSubsistenceThreshold(val=subsistence_threshold):
    global subsistence_threshold
    subsistence_threshold = float(val)
    return val

birth_rate = 1.0
def setBirthRate(val=birth_rate):
    global birth_rate
    birth_rate = float(val)
    return val

NEIGHBORHOOD_RADIUS = 1
move_cost = 1
def setMoveCost(val=move_cost):
    global move_cost
    move_cost = float(val)
    return val

fractional_move_cost = move_cost/L.width

# Helping methods;
communal_sharing = False  #communal sharing
def setCommunalSharing(val=False):
    global communal_sharing
    communal_sharing = bool(val)
    return val

grn_help = False
def setGRNHelp(val=grn_help):
    global grn_help
    grn_help = bool(val)
    return val

brn_help = False
def setBRNHelp(val=brn_help):
    global brn_help
    brn_help = bool(val)
    return val

world = None



class HHAgent(object):
    
    nextID=0
    first=None # a debug variable
    
    @staticmethod
    def reset():
        HHAgent.nextID=0
        HHAgent.first=None   
    
    def __init__(self, lineage=None):
        self.ID = HHAgent.nextID
        HHAgent.nextID +=1
        
        if lineage==None:
            self.lineage = self.ID
        else:
            self.lineage = lineage
            
        self.food_storage = 0
        self.age = 0
        self.commitments = {} # commitments to other households
        self.parents = []
        self.children = []
        self.adoptees = []  #extended family?
        self.nextBaby = None
        
    def adopt(self, forager):
        self.adoptees.append(forager)
        forager.joinHousehold(self)
    
    def addParent(self, parent):
        self.parents.append(parent)
        parent.joinHousehold(self)
        
    def addChild(self, child):
        self.children.append(child)
        child.joinHousehold(self)
    
    def removeMember(self, member):
        if self.parents.count(member) > 0:
            self.parents.remove(member)
        elif self.children.count(member) > 0:
            self.children.remove(member)
        elif self.adoptees.count(member) > 0:
            self.adoptees.remove(member)
    
    def combineWith(self, other):
        for child in other.children:
            self.addChild(child)
        self.food_storage += other.food_storage
        world.removeHousehold(other)
    
    def step(self):
        self.age += 1
        
        self.eat()  #may have received food shared by others
        self.evaluateAndMove()
        if self.isHungry():  #forage and eat if shared food was insufficient
            self.forage()
            self.eat()
        
        if self.isHungry():
            self.askNeighborsForHelp()
        
        if not self.hasDied():     
            self.dispositionExcess()
            self.makeABaby()
            
            for member in self.members():
                member.step()
        else:
            pass
        if self.food_storage <0:  #this is needed to eliminate floating point errors that are messing up the Hoover index
            self.food_storage = 0
                    
    def determineFoodNeeds(self):
        needs = 0
        for member in self.members():
            needs += member.foodRequired()
        return needs
    
    
    def forage(self):
        gathering = world.forageResources(self, self.foragingAbility())
        self.food_storage += gathering
    
    def eat(self):
        self.food_needs = self.determineFoodNeeds()
        if self.food_needs>0 :
            fraction = min([self.food_storage/self.food_needs, 1]) # clip at 1
            for member in self.members():
                amount = fraction*member.foodRequired()
                member.eat(amount)
                self.food_storage -= amount
    
    def isStarving(self):
        cost_to_forage = subsistence_threshold*self.costToMoveDelta((1,1))
        food_amount = (self.food_storage + world.resourcesAt(world.locationOf(self)))
        return self.isHungry() and food_amount < self.determineFoodNeeds() + cost_to_forage
    
    def isHungry(self):
        hungry = False
        for m in self.members():
            hungry = hungry or m.getHealth()<1.0
        return hungry
    
    def getBachelors(self):
        bachelors = []
        for member in self.members():
            if member.isBachelor():
                bachelors.append(member)
        return bachelors
                
    def makeABaby(self):
        if self.nextBaby != None :
            self.addChild(self.nextBaby)
            self.nextBaby = None
        if self.canMakeABaby() and rnd.random() < birth_rate:
            self.nextBaby = F.Forager(age=0, parents=self.parents)
    
    def canMakeABaby(self):
        if len(self.parents)==2:
            return not self.parents[0].isSenior() and not self.parents[1].isSenior()
        else :
            return False
        
    def askNeighborsForHelp(self):
        neighborhood = world.getNeighborhoodOf(self, radius=NEIGHBORHOOD_RADIUS)
        if len(neighborhood)==0:
            self.moveToRandomLocation()
            self.forage()
            self.eat()
        elif grn_help or brn_help:
            if grn_help:
                kin_neighbors = [hh for hh in neighborhood if self.kinshipWith(hh)]
                total_kin_storage = sum([hh.food_storage for hh in kin_neighbors])
                food_deficit = self.determineFoodNeeds() - self.food_storage
                if total_kin_storage > 0 and food_deficit > 0:
                    for kin_hh in kin_neighbors:
                        # kin proportionally share the burden of helping
                        amount = food_deficit*kin_hh.food_storage/total_kin_storage
                        kin_hh.requestFoodFor(self, amount)
                        self.eat()
            if brn_help and self.isStarving():
                nonkin_neighbors = [hh for hh in neighborhood if not self.kinshipWith(hh)]
                nonkin_neighbors = sorted(nonkin_neighbors, key=lambda neighbor: neighbor.debtTo(self))
                for neighbor in nonkin_neighbors:
                    food_deficit = self.determineFoodNeeds() - self.food_storage
                    if food_deficit > 0 :
                        amount = neighbor.requestFoodFor(self, food_deficit)
                        self.eat()
                    else :
                        break
                
    def requestFoodFor(self, other, food_deficit):
        amount = self.giveFoodTo(other, food_deficit)
        return amount

    def giveFoodTo(self,other, amount):
        amount = min([amount, self.food_storage])
        other.food_storage += amount
        self.food_storage -= amount
        if other!=self:  # can't have debts to one's self
            other.increaseCommitments(self, amount)
            world.reportFoodSharing(amount)
        return amount
        
    def increaseCommitments(self, other, amount):
        if (self.kinshipWith(other) and grn_help):  #GRN does not track commitment
            world.reportGRNSharing(amount)
        elif brn_help:
            if self not in other.commitments:
                other.commitments[self] = 0
            if other not in self.commitments:
                self.commitments[other] = 0
            self.commitments[other] += amount
            other.commitments[self] -= amount
            world.reportBRNSharing(amount)
        elif communal_sharing:
            world.reportCOMSharing(amount)
            

    def dispositionExcess(self):
        # this section was revised 12/9, see commented out code below for pre-revision code.
        # additional BRN sharing in this activity was only occurring *if*
        # communal_sharing was turned on.  This is logically inconsistent, since
        # BRN sharing is intended to be independent from communal sharing.
        neighborhood = world.getNeighborhoodOf(self, radius=1)#NEIGHBORHOOD_RADIUS)
        food_shared = self.food_storage - self.amountToSetAside()
        if neighborhood:
            # separate into debtors and everyone else
            neighborhood = sorted(neighborhood, key = lambda hh: hh.debtTo(self))
            if brn_help:
                debtees = [hh for hh in neighborhood if self.debtTo(hh)>0]            
                #pay back debts owed first
                for debtee in debtees:
                    if food_shared <= 0:
                        break
                    else :
                        amount = self.giveFoodTo(debtee, self.commitments[debtee])
                        food_shared -= amount
            #finally, share what's left, communally or with kin
            if communal_sharing:
                everyone_else = [hh for hh in neighborhood if hh.debtTo(self)>=0]
                everyone_else.append(self)  # we get to participate in the feast
                count = sum([hh.size() for hh in everyone_else])
                if food_shared>0 and count:
                    portion = food_shared/count
                    for neighbor in everyone_else:
                        self.giveFoodTo(neighbor, portion*neighbor.size())
            elif grn_help:
                kin = [hh for hh in neighborhood if self.kinshipWith(hh)]
                kin.append(self)
                count = sum([hh.size() for hh in kin])
                if food_shared>0 and count:
                    portion = food_shared/count
                    for neighbor in kin:
                        self.giveFoodTo(neighbor, portion*neighbor.size())
#   found a bug, old code as of 12/9
#         if communal_sharing:
#             neighborhood = world.getNeighborhoodOf(self, radius=1)#NEIGHBORHOOD_RADIUS)
#             food_shared = self.food_storage - self.amountToSetAside()
#             if neighborhood:
#                 # separate into debtors and everyone else
#                 neighborhood = sorted(neighborhood, key = lambda hh: hh.debtTo(self))
#                 debtors = [hh for hh in neighborhood if self.debtTo(hh)>0]
#                 everyone_else = [hh for hh in neighborhood if hh.debtTo(self)>=0]
#                 everyone_else.append(self)  # we get to participate in the feast
#                 #pay back debtors first
#                 for debtor in debtors:
#                     if food_shared <= 0:
#                         break
#                     else :
#                         amount = self.giveFoodTo(debtor, self.commitments[debtor])
#                         food_shared -= amount
#                 #finally, share what's left
#                 count = sum([hh.size() for hh in everyone_else])
#                 if food_shared>0 and count:
#                     portion = food_shared/count
#                     for neighbor in everyone_else:
#                         self.giveFoodTo(neighbor, portion*neighbor.size())
    
    def debtTo(self, other):
        if other in self.commitments:
            return self.commitments[other]
        else:
            return 0
    
    def prestige(self):
        sum = 0
        for hh in self.commitments.keys():
            sum -= self.commitments[hh]
        return sum
    
    def localPrestige(self):
        neighborhood = world.getNeighborhoodOf(self, radius=1)
        prestige = 0
        for neighbor in neighborhood:
            if neighbor in self.commitments:
                prestige += neighbor.commitments[self]
        return prestige
    
    def amountToSetAside(self):
        neighborhood = world.getNeighborhoodOf(self, radius=1)
        storage = 0
        for neighbor in neighborhood:
            if self in neighbor.commitments:
                storage += neighbor.commitments[self]
        storage = min([storage, self.food_storage])
        
        return storage
        
    def adults(self):
        return filter(lambda m: m.isAdult(), self.members())
    
    def members(self):
        members = []
        members.extend(self.parents)
        members.extend(self.children)
        members.extend(self.adoptees)
        
        return members
    
    def kinshipWith(self, other):
        my_kin_set = set()
        for member in self.members():
            my_kin_set = my_kin_set | member.traceAncestry()
        their_kin_set = set()
        for member in other.members():
            their_kin_set = their_kin_set | member.traceAncestry()
        return my_kin_set & their_kin_set
    
    
    
    def hasDied(self):
        deadlist = []
        for member in self.members():
            if member.hasDied():
                deadlist.append(member)
                world.reportADeath(member)
        for dead in deadlist:
            if dead.mate != None:
                dead.mate.mate = None
            self.removeMember(dead)
        return self.size()==0
            
    def size(self):
        return len(self.parents) + len(self.children) + len(self.adoptees)
    
    def foragingAbility(self):
        ability = 0
        for forager in self.members():
            if forager is not None:
                ability += forager.foragingExpertise()
        return ability
    
    def traverseTo(self, goal_location):
        goal_reached = False
        gx, gy = goal_location
        while not self.isStarving() and not goal_reached:
            lx, ly = world.locationOf(self)
            dx = gx - lx
            if dx!=0:
                dx = round(dx/abs(dx))
            dy = gy - ly
            if dy != 0:
                dy = round(dy/abs(dy))
            location = W.addlocs((lx,ly),(dx,dy))
#             location, resources = world.bestLocationAt(location)
            self.moveTo(location)
            self.forage()
            self.eat()
            if location==goal_location or not self.isHungry():
                goal_reached = True
    
    def costOfMoveBetween(self, old_location, new_location):
        return self.size()*(1+L.distanceBetween(old_location, new_location))*fractional_move_cost
    
    def costToMoveDelta(self, deltaXY):
        return self.size()*(1+L.distanceBetween((0,0), deltaXY))*fractional_move_cost 
    
    def moveTo(self, new_location):
        current_loc = world.locationOf(self)
        cost = self.costOfMoveBetween(current_loc, new_location)
        if current_loc!=new_location:
            world.moveHouseholdTo(self, new_location)
            self.dispositionExcess()
            self.food_storage = 0
        ind_cost = cost/self.size()
        for member in self.members():
            member.move(ind_cost)      
        
    def moveToAnotherLocation(self):
        location, resources = world.bestLocationAt(world.locationOf(self)) 
        self.moveTo(location)
        
    def moveToRandomLocation(self):
        location = (rnd.randrange(L.width),rnd.randrange(L.width))
        self.moveTo(location)
        
    def moveRandomDelta(self):
        d_loc = (rnd.randrange(3)-1,rnd.randrange(3)-1)
        location = world.locationOf(self)
        self.moveTo(W.addlocs(location, d_loc))
        
    def evaluateLocationAgainst(self, alternate_location):
        current_location = world.locationOf(self)
        cost_to_relocate = self.costOfMoveBetween(current_location, alternate_location)
        cost_to_stay = self.costOfMoveBetween(current_location, current_location)
        resources_here = world.resourcesAt(current_location)
        resources_there = world.resourcesAt(alternate_location)
        if grn_help:  #cognition about accounting for kin in where to move added 12/1
            neighborhood = world.getNeighborsAround(current_location, radius=1)
            kin_neighbors = [hh for hh in neighborhood if self.kinshipWith(hh)]
            total_kin_storage = sum([hh.food_storage for hh in kin_neighbors])
            resources_here += total_kin_storage
            neighborhood = world.getNeighborsAround(alternate_location, radius=1)
            kin_neighbors = [hh for hh in neighborhood if self.kinshipWith(hh)]
            total_kin_storage = sum([hh.food_storage for hh in kin_neighbors])
            resources_there += total_kin_storage - self.food_storage
            
        return (resources_there - cost_to_relocate) - (resources_here - cost_to_stay)
    
    def evaluateAndMove(self):
        current = world.locationOf(self)
        new_location = current
        best_resource_location, best_resources = world.bestLocationAt(world.locationOf(self))
        if best_resource_location!=current:
            if self.evaluateLocationAgainst(best_resource_location) > 0:
                new_location = best_resource_location
        self.moveTo(new_location)
        

"""
MAIN
"""
if __name__ == '__main__':
    import foraging_simGUI as sim
    sim.run()   
    