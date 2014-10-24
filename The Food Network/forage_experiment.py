import world as W
import landscape as L
import hhagent as HH
import forager as F
import datetime as DT
import utility as U
import collections
import experiment as exp

runtime = 0
no_pop = -1
pop_explosion = 1

setters = []
setters.append(L.setGridLength)
setters.append(W.setMinResource)
setters.append(W.setMaxResource)
setters.append(W.setRegrowthSteps)
setters.append(W.setStartingPopulation)
setters.append(F.setAvgForagingExpertise)
setters.append(F.setSdvForagingExpertise)
setters.append(HH.setBirthRate)
setters.append(HH.setCommunalSharing)
setters.append(HH.setGRNHelp)
setters.append(W.setKinSpan)
setters.append(HH.setBRNHelp)

class ForageExperiment(exp.Experiment):
     
    def __init__(self):
        super().__init__()
        print("Initializing landscape for job")
        self.metrics_start = 250
        self.landscape = None
        self.sim_runtime = 1000

    def initiateSim(self):
        if self.landscape==None:
            self.landscape=L.Landscape()
        self.theWorld = W.World(size=L.width, numagents= W.starting_agents, landscape=self.landscape)
        self.time = 0
        self.max_prestige = []
        self.avg_prestige = []
    
    def stepSim(self):
        self.time += 1
        self.theWorld.step()
        self.max_prestige.append(max(self.theWorld.hh_prestige))
        self.avg_prestige.append(U.mean(self.theWorld.hh_prestige))
    
    def stopSim(self):
        if self.time>=self.sim_runtime:
            self.stop_condition = runtime
            return True
        if self.theWorld.population==0:
            self.stop_condition = no_pop
            return True
        if (self.time>200 and (self.theWorld.population>3000 or self.theWorld.avg_pop_100[-1]>1500)):
            self.stop_condition = pop_explosion
            return True
        if (self.theWorld.population>5000):
            self.stop_condition = pop_explosion
            return True
        return False
    
    def setupSimFuncs(self):
        self.simInitFunc = self.initiateSim 
        self.simStepFunc = self.stepSim
        self.simStopFunc = self.stopSim 
        
    """
    Override this method in subclasses, with the sections completed.
    """
    def setupExperiment(self):   
        """
        Section 1 - Experiment name and comments; describe the experiment.
        """
        self.Name = "Unnamed"  # this should be compatible with file names
        self.comments = ""
        
        self.setupSimFuncs()
        
        self.addParameter(L.setGridLength, [2])
        self.addParameter(W.setMinResource, [2])
        self.addParameter(W.setMaxResource, [8])
        self.addParameter(W.setRegrowthSteps, [8])
        self.addParameter(W.setStartingPopulation, [256])
        self.addParameter(F.setAvgForagingExpertise, [1.3])
        self.addParameter(F.setSdvForagingExpertise, [0.1])
        self.addParameter(HH.setBirthRate, [1.0])
        self.addParameter(HH.setCommunalSharing, [False])
        self.addParameter(HH.setGRNHelp, [False])
        self.addParameter(W.setKinSpan, [2])
        self.addParameter(HH.setBRNHelp, [False])
        
        self.job_repetitions = 2
        
    def avg_pop(self):
        return U.mean(self.theWorld.populations[self.metrics_start:])
    
    def hh_age(self):
        return self.theWorld.avg_hh_age[-1]
    
    def med_life(self):
        return U.median(self.theWorld.ages_at_death)
    
    def avg_life(self):
        return  U.mean(self.theWorld.ages_at_death)
    
    def adult_med_life(self):
        return  U.median(self.theWorld.adult_ages_at_death)
    
    def adult_avg_life(self):
        return  U.mean(self.theWorld.adult_ages_at_death)
    
    def std_pop(self):
        return  U.standardDeviation(self.theWorld.populations[self.metrics_start:])
    
    def max_run_prestige(self):
        return max(self.max_prestige[self.metrics_start:])
    
    def avg_run_prestige(self):
        return U.mean(self.avg_prestige[self.metrics_start:])
    
    def avg_median_stored(self):
        return  U.mean(self.theWorld.median_storage[self.metrics_start:])
    
    def avg_avg_hoover(self):
        return  U.mean(self.theWorld.avg_hoover[self.metrics_start:])
    
    def avg_max_hoover(self):
        return  U.mean(self.theWorld.max_hoover[self.metrics_start:])
    
    def avg_stored(self):
        return U.mean(self.theWorld.avg_food_stored[self.metrics_start:])
        
    def avg_shared(self):
        return  U.mean(self.theWorld.food_shared[self.metrics_start:])
    
    def com_shared(self):
        return  U.mean(self.theWorld.com_sharing[self.metrics_start:])
    
    def grn_shared(self):
        return  U.mean(self.theWorld.grn_sharing[self.metrics_start:])
    
    def brn_shared(self):
        return  U.mean(self.theWorld.brn_sharing[self.metrics_start:])        
    
    def getTime(self):
        return self.time
    
    def getStopCondition(self):
        return self.stop_condition
    
    def setupOutputs(self):
        #######################################################################
        """
        Section 4 - Add getter methods, names, and string formats so the automater
        can retrieve and record metrics from your simulation.
        
        #template
        self.addOutput(getterFunction, output_name, output_format)
        
        #Example:
        self.addOutput(getAveragePopulation, "Avg Pop.", "%8.4f")
        # getAveragePopulation() returns the average population of the sim run,
        # and the header "Avg Pop." will be written to the file
        """
        self.addOutput(self.avg_pop, "avg pop.", "%9.5f")
        self.addOutput(self.std_pop, "sdv pop", "%9.5f")
        self.addOutput(self.hh_age, "hh age", "%5.3f")
        self.addOutput(self.avg_life, "avg life", "%5.3f")
        self.addOutput(self.med_life, "med life", "%5.3f")
        self.addOutput(self.adult_avg_life, "adult avg life", "%5.3f")
        self.addOutput(self.adult_med_life, "adult med life", "%5.3f")
        self.addOutput(self.avg_median_stored, "avg median stored", "%7.3f")
        self.addOutput(self.avg_avg_hoover, "avg avg hoover", "%6.5f")
        self.addOutput(self.avg_max_hoover, "avg max hoover", "%6.5f")
        self.addOutput(self.max_run_prestige, "max prestige", "%9.4f")
        self.addOutput(self.avg_run_prestige, "avg prestige", "%9.4f")
        self.addOutput(self.avg_stored, "avg stored", "%8.4f")
        self.addOutput(self.avg_shared, "avg shared", "%8.4f")
        self.addOutput(self.com_shared, "com shared", "%8.4f")
        self.addOutput(self.grn_shared, "grn shared", "%8.4f")
        self.addOutput(self.brn_shared, "brn shared", "%8.4f")
        self.addOutput(self.getTime, "runtime", "%5d")
        self.addOutput(self.getStopCondition, "stop cond.", "%2d")

if __name__ == '__main__':
    ForageExperiment().run()     