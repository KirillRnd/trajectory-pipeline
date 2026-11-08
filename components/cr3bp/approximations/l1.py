"""Definitions extracted unchanged from source/L1_approx.py."""
import math
import numpy as np

def odeCR3BP(t, p, mu):
    R = np.sqrt((p[0] + mu)**2 + p[1]**2)
    r = np.sqrt((p[0] - 1 + mu)**2 + p[1]**2)
    dpdt = np.array([p[2], p[3],
    2 * p[3] + p[0] - (1 - mu) * (p[0] + mu) / R**3 - mu * (p[0] - 1 + mu) / r**3,
    -2 * p[2] + p[1] - (1 - mu) * p[1] / R**3 - mu * p[1] / r**3])

    return dpdt

mu = 0.012150584460351

x1_fun = lambda x: x

x2_fun = lambda x: 0

x1_fun = lambda x: x

x2_fun = lambda x: 0

L1 = 0.836915131427382

def v1_fun(x):
    return 0

def v2_fun(x):
    x = L1 - x
    if x>=0 and x<0.02101619: #ближняя к L1 область
        y = (math.tanh(x*(-x*math.sin(232.584703325996*x - 426.066914410504) + 155.62958*x**1.178488 + 8.4041856317918))) #1.5e-05
    elif x>=0.02101619 and x<0.11879741:
        y = (x + (x**1.5540553 + 0.21916248)*(math.atan(math.atan((0.99317352*x - 0.032829714130959)/x)) + 1.3207281)) #4.5e-05
    elif x>=0.11879741:       #дальняя от L1 область
        y = 2.0*x*(2.0260577*x + math.cos((2.49849589685834*x - 0.99438343847612 + 0.0917029035952107/x)*math.log(x)))**x + 0.35522524 #2.8e-06
    else: 
        y = 0
    return y

def T_fun(x):
    x = L1 - x
    y = (-x + 1.0281601*math.atan(32.262*x)**3.399058 + math.atan(3.7499506*(x + 0.053125296)*math.atan(41.577175*x**2)) + 2.694211) #4.5e-03
    return y
