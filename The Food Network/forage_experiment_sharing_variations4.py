import world as W
import landscape as L
import hhagent as HH
import forager as F
import forage_experiment as exp

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

class ForageExperimentVariation(exp.ForageExperiment):
     
    def __init__(self):
        super().__init__()
        
    """
    Override this method in subclasses, with the sections completed.
    """
    def setupExperiment(self):   
        """
        Section 1 - Experiment name and comments; describe the experiment.
        """
        self.Name = "forage-sensitivity-sharing-4"  # this should be compatible with file names
        self.comments = "\nTaking data on all combinations of sharing, with kinship span=6."
        self.comments += "\nYet another because of corrected hoover metric."
        
        self.setupSimFuncs()
        
        self.addParameter(L.setGridLength, [2])
        self.addParameter(W.setMinResource, [2])
        self.addParameter(W.setMaxResource, [8])
        self.addParameter(W.setRegrowthSteps, [8])
        self.addParameter(W.setStartingPopulation, [256])
        self.addParameter(F.setAvgForagingExpertise, [1.3])
        self.addParameter(F.setSdvForagingExpertise, [0.1])
        self.addParameter(HH.setBirthRate, [0.2])
        self.addParameter(HH.setMoveCost, [5.0])
        self.addParameter(HH.setCommunalSharing, [False, True])
        self.addParameter(HH.setGRNHelp, [False, True])
        self.addParameter(W.setKinSpan, [6])
        self.addParameter(HH.setBRNHelp, [False, True])
        
        self.job_repetitions = 20

if __name__ == '__main__':
    ForageExperimentVariation().run()     