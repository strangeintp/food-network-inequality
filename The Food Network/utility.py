import datetime as DT
import random
import math

#a utility function that can generate a random number using a normal distribution with lower and upper bounds
def randomBoundedNormal(meanVal,stdDev,lowerBound,upperBound):
    aRand = random.gauss(meanVal,stdDev) # could also use: normalvariate()but gauss () is slightly faster.
    while (aRand < lowerBound or aRand > upperBound):
        aRand = random.gauss(meanVal,stdDev)
    return aRand

def GenBoundedRandomNormal(meanVal,stdDev,lowerBound,upperBound):
    aRand = random.gauss(meanVal,stdDev) # could also use: normalvariate()but gauss () is slightly faster.
    while (aRand < lowerBound or aRand > upperBound):
        aRand = random.gauss(meanVal,stdDev)
    return aRand

def mean(values):
    if values:
        return sum(values)/len(values)
    else:
        return 0

def variance(values):
    mu = mean(values)
    square_diffs = [(value-mu)**2 for value in values]
    return mean(square_diffs)

def standardDeviation(values):
    return math.sqrt(variance(values))

def median(values):
    if not values:
        return 0
    sorted_values = sorted(values, key=lambda x: x)
    mid_idx=int(len(sorted_values)/2)
    return sorted_values[mid_idx]

def HooverIndex(values):
    avg = mean(values)
    sum_values=sum(values)
    if sum_values==0:
        return 0
    above_avg = list(filter(lambda x:x>avg, values))
    above_avg_sum = sum(above_avg)-avg*len(above_avg)
    return above_avg_sum/sum_values

def GiniIndex(values):
    val_sort = sorted(values, key=lambda val: val)
    n = len(values)
    sum_iy = sum([i*val_sort[i] for i in range(n)])
    sum_y = sum(val_sort)
    gini = 2*sum_iy/(n*sum_y) - (n+1)/n
    return gini

def getTimeStampString():
    dt = DT.datetime.now()    
    timestamp_str = str(dt.year) + "-" + str("%02d"%dt.month) + "-"
    timestamp_str += str("%02d"%dt.day) + " " + str("%02d"%dt.hour)
    timestamp_str += str("%02d"%dt.minute) + str("%02d"%dt.second)
    return timestamp_str

"""
MAIN
"""
if __name__ == '__main__':
    a = [2**i for i in range(10)]
    print(a)
    print("Hoover:\t%5.4f"%HooverIndex(a))
    print("Gini:\t%5.4f"%GiniIndex(a))
    a = [-10,0,0,0,0,0,0,0,0,100]
    print(a)
    print("Hoover:\t%5.4f"%HooverIndex(a))
    print("Gini:\t%5.4f"%GiniIndex(a))