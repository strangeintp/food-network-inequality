import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import pylab as PL
import random as RD
import world as W
import landscape as L
import forage_experiment as EXP
import os
import datetime as DT
import pycxsimulator as sim

RD.seed()

greenstart = (0.0,  0.0, 0.0)
cdict = {'red':   [(0.0,  0.0, 0.0),
                   (1.0,  0.0, 0.0)],
    
         'green': [greenstart,
                   (1.0,  1.0, 1.0)],
    
         'blue':  [(0.0,  0.0, 0.0),
                   (1.0,  0.0, 0.0)]}

pSetters = []
dirNames = []

MOVIES=0

def openFolder():
    global dirName, dirNames, files
    timestamp = str(DT.datetime.now())
    timestamp = "".join(list(filter(lambda c: c>='0' and c<='9', timestamp)))
    dirName = "Images_" + timestamp
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    dirNames.append(dirName)
    files = []

def init():
    global time, theWorld, cmap, plots, dirName, num_households, times
    l=L.Landscape()
    theWorld = W.World(size=L.width, numagents= W.starting_agents, landscape=l)
    
    time = 0
    num_households = [len(theWorld.households)]
    times =[0]
    
    cmap = matplotlib.colors.LinearSegmentedColormap(name='G', segmentdata=cdict, N=256)
    plots = None
    if MOVIES:
        openFolder()
    
def draw(figure):
    global resources, time, theWorld, cmap, files
    PL.cla()
    
    cmap.set_under()
    PL.pcolormesh(theWorld.foraging_resources, cmap = cmap, vmin=0,
                  vmax=W.max_resource)
    PL.axis('scaled')
    PL.hold(True)
    xyp = zip(*[theWorld.hh_locations[hh] for hh in theWorld.households])
    xy = [list(t) for t in xyp]
    
    if len(xy)>0:
        x = [i+0.5 for i in xy[0]]
        y = [i+0.5 for i in xy[1]]
        lineage = [hh.lineage for hh in (theWorld.households)]
        hh_size = [20*hh.size() for hh in (theWorld.households)]
        PL.scatter(y, x, c = lineage, s=hh_size, vmin=0, vmax=W.starting_agents, cmap = plt.get_cmap('hsv'))
        message = r't = {0}     Pop.: {1}     HHs: {2}    max HHs: {3}'
        PL.title(message.format(time, theWorld.population, len(theWorld.households), max(lineage))) 
    PL.hold(False)
    figure.tight_layout()
    if MOVIES:
        fname = dirName+('\\_temp%05d.png'%time)
        figure.savefig(fname)
        files.append(fname)
    drawPlots()

def drawPlots():
    global plots, theWorld, time, times, num_households
    
    if plots == None or plots.canvas.manager.window == None:
        plots = PL.figure(2)
        PL.ion()
    PL.figure(2)
    PL.hold(True)
    PL.subplot(4, 3, 1)
    PL.cla()
    tot = theWorld.food_shared_totals
    food_shared_avg = [tot[i]/(i+1) for i in range(len(tot))]
    PL.plot(food_shared_avg, color = 'black')
    PL.plot(theWorld.food_shared, color = 'pink')
    PL.plot(theWorld.brn_sharing, color = 'brown')
    PL.plot(theWorld.grn_sharing, color = 'green')
    PL.title("Food shared each year (BRN, GRN, tot) and average")
    PL.hold(True)
    PL.subplot(4, 3, 2)
    PL.cla()
    interval = 20
    step = 0.5
    b = [-interval+step*i for i in range(2*int(interval/step)+1)]
    if theWorld.hh_prestige:
        PL.hist(theWorld.hh_prestige, bins=b, color='brown')
        PL.title("hh count by prestige")
    PL.hold(True)
    PL.subplot(4, 3, 3)
    PL.cla()
    PL.plot(theWorld.populations, color = 'pink')
    PL.plot(theWorld.avg_pop, color = 'black')
    PL.plot(theWorld.avg_pop_100, color = 'blue')
    PL.title("Population, average, and 100-year average")
    PL.hold(True)
    PL.subplot(4, 3, 4)
    PL.cla()
    PL.plot(theWorld.avg_ages, color = 'pink')
    PL.plot(theWorld.avg_adult_ages, color = 'red')
    PL.plot(theWorld.avg_hh_age, color = 'black')
    PL.title("Average household(black), forager(pink), and adult forager age (red) at end")
    PL.hold(True)
    PL.subplot(4, 3, 5)
    PL.cla()
    interval = (W.max_founder_kin_span-W.min_founder_kin_span)
    step = 0.1
    b = [(W.min_founder_kin_span + step*i) for i in range(int(interval/step)+1)]
    if theWorld.kinship_spans:
        PL.hist(theWorld.kinship_spans, bins=b, color='blue')
#     PL.axis()
        PL.title("population count by kinship span")
    PL.hold(True)
    PL.subplot(4, 3, 6)
    PL.cla()
    interval = (W.max_founder_kin_span-W.min_founder_kin_span)
    step = 1
    b = [(W.min_founder_kin_span + step*i) for i in range(int(interval/step)+1)]
    if theWorld.kinship_spans:
        PL.hist(theWorld.kinship_spans, bins=b, color='blue')
#     PL.axis()
        PL.title("population count by kinship span")
    PL.hold(True)
    PL.subplot(4, 3, 7)
    PL.cla()
    interval = 10
    step = 0.05
    b = [step*i for i in range(int(interval/step)+1)]
    if theWorld.hh_food_stored:
        PL.hist(theWorld.hh_food_stored, bins=b, color='cyan')
#     PL.axis()
        PL.title("hh counts by food stored")
    PL.hold(True)
    PL.subplot(4, 3, 8)
    PL.cla()
    interval = max(theWorld.pop_expertise) - min(theWorld.pop_expertise)
    step = 0.05
    b = [min(theWorld.pop_expertise) + step*i for i in range(int(interval/step)+1)]
    if theWorld.pop_expertise:
        PL.hist(theWorld.pop_expertise, bins=b, color='cyan')
#     PL.axis()
        PL.title("population counts by foraging expertise")
    PL.hold(True)
    PL.subplot(4, 3, 9)
    PL.cla()
    PL.plot(theWorld.median_storage, color = 'black')
    PL.title("Median food stored")
    PL.hold(True)
    PL.subplot(4, 3, 10)
    PL.cla()
    PL.plot(theWorld.hoover, color = 'black')
    PL.title("Hoover index")
    PL.hold(True)
    PL.subplot(4, 3, 10)
    PL.cla()
    PL.plot(theWorld.avg_food_stored, color = 'black')
    PL.title("average food stored")
    PL.hold(False)
    plots.tight_layout()
    plots.canvas.manager.window.update()
    PL.figure(1)

def step():
    global time, theWorld, times, num_households
    time += 1
    times.append(time)
    theWorld.step() 
    num_households.append(len(theWorld.households))
    
def stop():
    global time, theWorld
    return time>=10000 or len(theWorld.households)==0

def run():
    pSetters = EXP.setters
    simfuncs = [init, draw, step, stop]
    sim.GUI(parameterSetters = pSetters, interval=1,stepSize=1).start(func=simfuncs)
    
"""
MAIN
"""
if __name__ == '__main__':
    run()