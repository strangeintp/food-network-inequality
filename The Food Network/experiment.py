import utility as U
import datetime as DT
import collections
import sys


"""  
An automated experimenter for running parameter sweeps/variations for discrete-
time-stepped simulations.  Outputs job results to console and file in .csv
format.

This class should not be instantiated.
Instead, it should be subclassed with one method override:
1) setupExperiment() -- see comments for that method below.

Also, be sure to call self.init() within your constructor, or the collections
will not be initialized, and you will get "attribute not found" errors.
Python does not initialize variables for subclasses in superclass constructors.
This is an annoying design feature of OOP in Python, if you ask me.

This automater will automatically calculate averages and standard deviations
over job repetitions for each job, for each of the output variables you've specified.
Modify the run() method if you need more.

- Vince Kane, 29 Nov 2013
"""
class Experiment(object):
    
    """ 
    You will need to call self.init() within your constructor as well.
    super() does not work for constructors in python,  x(
    """  
    def __init__(self):
        self.init()
    
    def init(self):        
        self.paramSetters = collections.OrderedDict()
        self.defaults = collections.OrderedDict()
        """ A dictionary of getter methods, accessed by a name for the variable """
        self.output_getters = collections.OrderedDict()
        """ A dictionary of string formats that tells the fileWriteOutput method how to format the output values"""
        self.output_formats = collections.OrderedDict()
        self.fileName = ""
        
    """
    Override this method in subclasses, with the sections completed.
    """
    def setupExperiment(self):   
        """
        Section 1 - Experiment name and comments; describe the experiment.
        """
        self.Name = "Unnamed"  # this should be compatible with file names
        self.comments = ""
        
        #######################################################################
        """
        Section 2 - Simulation behavior methods.
        """
        """ Method that sets up each simulation run/job-repetition """
        self.simInitFunc = None  # replace 'None' with your method
        """ The method that will be called each step of the simulation."""
        self.simStepFunc = None # replace 'None' with your method
        """ Function should return True to halt the while loop that steps the simulation """
        self.simStopFunc = None # replace 'None' with your method
        
        #######################################################################
        """
        Section 3 - Add model parameters setters and defaults or variations.
        Note that this automater implements a full factorial design, 
        so three parameters with a sweep of three values each generates 27 jobs.
        (And each job is repeated x times.)
        
        #template
        self.addParameter(setterMethod, values)
        if values is singular (non-iterable or list length==1), 
        the parameter is set for all jobs in the experiment.
        #Examples:
        
        self.addParameter(setInitialPopulation, 100)  
        # sets a default with setInitialPopulation(100)
        
        self.addParameter(setInitialPopulation, [100, 200])  
        # includes setInitialPopulation in the full factorial design, 
        # with parameter values of 100 and 200.  
        """
        
        """ 
        Section 3.5 - Number of repetitions per job.
        """
        self.job_repetitions = 1
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
          
    def addParameter(self, setterMethod, values):
        if not isinstance(values, list):
            self.defaults[setterMethod] = values
        elif len(values)==1:
            self.defaults[setterMethod] = values[0]
        else:
            self.paramSetters[setterMethod] = values
            
    def addOutput(self, getterFunction, output_name, output_format):
        self.output_getters[output_name] = getterFunction
        self.output_formats[output_name] = "," + output_format
    
    def setupFile(self):
        dt = U.getTimeStampString()
        self.fileName = self.Name + " " + dt + ".csv"
        message = "Experiment " + self.Name
        message += "\n" + self.comments
        message += ".\nExperiment started %s\n"%dt
        self.output(message)
    
    def checkParameters(self):
        if not self.paramSetters:
            self.output("There are no variants to combine.  A single job will run, with the defaults.")
            for setter in self.defaults:
                self.paramSetters[setter] = [self.defaults[setter]]
        
    def run(self):
        self.setupExperiment()
        self.setupOutputs()
        self.setupFile()
        self.checkParameters()
        self.setDefaults()
        self.design = self.full_factorial_design(self.paramSetters, job_id_name = "job_id")
        self.filewriteParameters()
        try:
            self.simulate()
        except:
            error = sys.exc_info()[0]
            self.output("Experiment halted on error: %s" % error)
        finally:
            ### close out
            self.output("\n######################################################")
            self.output("\nExperiment Completed %s"%U.getTimeStampString())
            self.output("\n######################################################\n\n")
            self.outputFile.close()
        
    def simulate(self):
        for job in self.design:
            self.setJobParameters(job)
            job_outputs = collections.OrderedDict()  # a dictionary accessed by output variable name
            # initialize empty lists to track repetition outputs for each output variable
            for output in self.output_getters:
                job_outputs[output] = []
            for i in range(self.job_repetitions):
                self.simInitFunc()
                while not self.simStopFunc():
                    self.simStepFunc()
                outputs = self.getOutputs()
                for output in outputs:
                    job_outputs[output].append(outputs[output])
                self.outputFile.write("\n")
                self.fileWriteOutputs(outputs)
                
            # write statistics to file
            averages = collections.OrderedDict()
            stddevs = collections.OrderedDict()
            for variable in job_outputs:
                averages[variable] = U.mean(job_outputs[variable])
                stddevs[variable] = U.standardDeviation(job_outputs[variable])
            self.output("\naverages: ")
            self.fileWriteOutputs(averages)
            self.output("\nstandard deviations: ")
            self.fileWriteOutputs(stddevs)
        
    def getOutputs(self):
        outputs = collections.OrderedDict()
        for getter_name in self.output_getters:
            getter = self.output_getters[getter_name]
            outputs[getter_name] = getter()
        return outputs
    
    def fileWriteOutputs(self, outputs):
        message = ""
        for variable in outputs:
            message += self.output_formats[variable]%outputs[variable]
        self.output(message)
    
    def output(self, message):
        print(message)
        try:
            self.outputFile = open(self.fileName, 'a+')
            if self.outputFile != None:
                self.outputFile.write(message)
        except:
            print("Could not open output file for writing: %s" % sys.exc_info()[0])
    
    def filewriteParameters(self):        
        self.output("\n######################################################")
        self.output("\nExperiment Defaults:")
        for setter in self.defaults:
            message = "\n"
            message += "%40s"%setter.__name__
            message += " :,  \t"
            value = self.defaults[setter]
            message += str(value)
            self.output(message)
        self.output("\nExperiment Parameter Variations:")
        for setter in self.paramSetters:
            message = "\n"
            message += "%40s"%setter.__name__
            message += " :,  \t"
            value = self.paramSetters[setter]
            message += str(value)
            self.output(message)
        self.output("\n######################################################")
    
    def setDefaults(self):
        for setter in self.defaults:
            # call the method with the value indexed by the method name in the defaults dictionary
            setter(self.defaults[setter])
     
    def setJobParameters(self, job):
        self.output("\n")
        self.output("*********************Job Settings*********************")
        for setter in self.paramSetters:
            v = setter(job[setter])
            self.output("\n%40s"%setter.__name__ + " :\t,%s"%str(v))
        job_output_header = "\n"
        for variable_name in self.output_getters:
            job_output_header += ", " + variable_name
        self.output(job_output_header)

    def full_factorial_design(self, parameters, job_id_name = "job_id"):
    # Vince Kane note:  function provided by:
    # *** Library for experiment designs generation ***
    #
    # Copyright 2013 Przemyslaw Szufel & Bogumil Kaminski
    # {pszufe, bkamins}@sgh.waw.pl
        if not isinstance(parameters, collections.OrderedDict):
            raise Exception("parameters must be OrderedDict")
    
        counter = [0] * len(parameters)
        maxcounter = []
    
        for dimension in parameters:
            if not isinstance(parameters[dimension], list):
                raise Exception("dimension must be a list")
            if dimension == job_id_name:
                raise Exception("dimension name equal to job_id_name")
            maxcounter.append(len(parameters[dimension]))
        result = []
        go = True
        job_id = 0
        while go:
            job_id += 1
            job = collections.OrderedDict()
            i = 0
            for dimension in parameters:
                job[dimension] = parameters[dimension][counter[i]]
                i += 1
            job[job_id_name] = job_id
            result.append(job)
            for i in range(len(parameters) - 1, -1, -1):
                counter[i] += 1
                if counter[i] == maxcounter[i]:
                    counter[i] = 0
                    if (i == 0):
                        go = False
                else:
                    break
        return result
     
        
