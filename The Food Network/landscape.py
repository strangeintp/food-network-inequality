import matplotlib
matplotlib.use('TkAgg')

import pylab as PL
import random as RD
import scipy as SP
import math

RD.seed()

width = 50
loci_weight = 10

grid_length = 2
def setGridLength(val=grid_length):
    global grid_length
    val = float(val)
    grid_length = val
    return val

use_grid = 1
cmin = 0.1
pct_loci = 0.01
cont = True

class Landscape(object):
    
    def __init__(self):
        self.values = SP.zeros([width, width])
        self.loci = []
        self.loci_values = dict()
        
        if grid_length > 0:
            f = 1/grid_length
            grid_lines = [f*i+f/2 for i in range(int(grid_length))]    
            for i in grid_lines:
                for j in grid_lines:
                    y = int(j*(width))
                    x = int(i*(width))
                    c = (i-f/2)+(j-f/2)
                    if c==0:
                        c=cmin
                    if grid_length==1:
                        c=1.0
                    self.values[x,y] = c
                    locus = (x,y)
                    self.loci.append(locus)
                    self.loci_values[locus] = c
            self.generateWithLoci()
        elif grid_length<0:
            if grid_length>-1:
                pct_loci = -grid_length
                loci_number = int(pct_loci*width*width)
            else:
                loci_number = -int(grid_length)
            for i in range(loci_number):
                y = RD.randrange(width)
                x = RD.randrange(width)
                c = RD.random()*(1-cmin)+cmin
                self.values[x,y] = c
                locus = (x,y)
                self.loci.append(locus)
                self.loci_values[locus] = c
            self.generateWithLoci()
        else:
            self.values = SP.ones([width, width])
        
    def generateWithLoci(self):
        cont = True
        # set the landscape up
        while cont :
            cont = False
            tmp = self.values.copy()
            for x in range(width):
                for y in range(width):
                    if self.values[x,y]>0:
                        c = 0
                        dx = RD.randint(-1, 1)
                        dy = RD.randint(-1, 1)
                        x0 = (x+dx)%width
                        y0 = (y+dy)%width
                        if self.loci.count((x0,y0))==0:
                            sumweights = 0
                            for ddx in range(-1,2):
                                for ddy in range(-1,2):
                                    x1 = (x0+ddx)%width
                                    y1 = (y0+ddy)%width
                                    if self.loci.count((x1,y1))==0:
                                        c += self.values[x1,y1]
                                        sumweights += 1
                            for locus in self.loci:
                                weight = loci_weight/(self.distanceBetween((x0,y0),locus)**2)
                                c += self.loci_values[locus]*weight
                                sumweights+=weight
                            tmp[x0,y0] = c/sumweights
                            
                        #tmp[y0,x0] = 1
                    else :
                        cont = True 
            self.values = tmp
        
    def distanceBetween(self,p0, p1):
        x0, y0 = p0
        x1, y1 = p1
        dx = abs(x0 - x1)
        if dx > width/2 :
            dx = width-dx
        dy = abs(y0 - y1)
        if dy > width/2:
            dy = width-dy
        d = math.sqrt(dx**2 + dy**2)
        
        return d

    def getClosestLocus(self, p):
        
        loci_sorted = sorted(self.loci, key=lambda l: self.distanceBetween(p,l))
        locus = loci_sorted[0]
        
        return locus
    
    def normalizeTo(self, max_norm = 1.0, min_norm = 1.0):
        tmp = self.values.copy()
        for x in range(width):
            for y in range(width):
                tmp[x,y] = self.values[x,y]*(max_norm - min_norm) + min_norm
                
        return tmp

def dsquaredBetween(p0,p1):
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x0 - x1)
    if dx > width/2 :
        dx = width-dx
    dy = abs(y0 - y1)
    if dy > width/2:
        dy = width-dy
    d = dx**2 + dy**2
    
    return d
    
def distanceBetween(p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    dx = abs(x0 - x1)
    if dx > width/2 :
        dx = width-dx
    dy = abs(y0 - y1)
    if dy > width/2:
        dy = width-dy
    d = math.sqrt(dx**2 + dy**2)
    
    return d