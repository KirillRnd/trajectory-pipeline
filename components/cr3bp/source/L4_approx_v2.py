import numpy as np
from matplotlib import pyplot as plt
from scipy.integrate import solve_ivp
import math

def odeCR3BP(t, p, mu):
    R = np.sqrt((p[0] + mu)**2 + p[1]**2)
    r = np.sqrt((p[0] - 1 + mu)**2 + p[1]**2)
    dpdt = np.array([p[2], p[3],
    2 * p[3] + p[0] - (1 - mu) * (p[0] + mu) / R**3 - mu * (p[0] - 1 + mu) / r**3,
    -2 * p[2] + p[1] - (1 - mu) * p[1] / R**3 - mu * p[1] / r**3])

    return dpdt


mu = 1/82

x1 = lambda a: np.cos(a + np.pi/3) - mu
x2 = lambda a: -np.sin(a + np.pi/3)

def v1(a):
    if a<0.5 and a>=0:
        x = ((-0.021469986*a - 0.0003111248*math.log(a) - 0.0014662967)*math.cos(4.2054663*a**2.4511335)) #1.1e-05
    elif a>=0.5 and a<1.7:
        x = (0.0148235485*a*(3.7456698*a**2 - math.cos(a)) - 0.0148235485*math.exp(a*math.cos((a - 1.1082239)*(a**1.4377148 + 3.5604722)))) #6.1e-4
    elif a>=1.7 and a<2.8:
        x = ((a + math.log(a))*(a*(-0.059331506*a + 1.63273748380587e-7*math.exp((a - 0.5849132)**a) + 0.34727088) - 0.3137545) + 0.038643904) #1.3e-4
    else:
        x = (-a*np.exp(-3.6822217*a**(-2.8971705) - 1.238104*a**3.7654412) + 0.046486337*a - 0.0993868964965362*a*np.exp(-a))
    return x
def v2(a):
    if a<0.5 and a>=0:
        x =  (a*(0.057326578*a*math.cos(3.8822086*a - 2.3752067705845) + 0.0466879)) #7.3e-06
    elif a>=0.5 and a<1.7:
        x =  (0.0792431078064456*(a*(-0.191229236651487*math.cos(6.225616*a) 
                                     + math.exp(-0.036783073*math.cos(14.072274*a)*math.cos(2.849237*a - 0.6214909))))**1.4583089) #4.8e-4
    elif a>=1.7 and a<2.8:
        x = (a*(0.31209984*a + (-0.07542186*a + 0.026630582*math.exp(a) + 0.56088626)*math.cos(a)) - 0.58147573) #5.8e-5
    else:
        x =  (-0.02230581*(np.exp(a) + np.exp(np.cos((a**2)**0.95246226 - 1.3307008))*np.cos(3.6634598*a))*np.cos(2.0136378*a) + 0.052785624)
    return x
def T(a):
    if a<0.5 and a>=0:
        x =  (a**1.97235084*(-0.94786483*a + 0.798210717383035*a**a*math.cos(6.512141*a) + 1.13389117016559) + 21.027468) #6.9e-05
    elif a>=0.5 and a<1.7:
        x = (a + 0.2820783*math.exp(math.cos(4.1242228*a**1.7214167)) - math.cos(a) - math.cos(a*(a + 0.19541843)) + math.cos(4.0326896*a + 0.918334923647024) + 22.964064) #7.4e-3
    elif a>=1.7 and a<2.8:
        x = (1.0*math.log((a - 0.055466864)**(-1.4048711) - 2998199322.79278*math.exp(a)**(-16.559324)) - 2.06719275110082e-13*math.cos(a - 1.4642737)**(-16.55932) + 26.737839) #7.7e-4
    else:
        x = (-8.61150672305524*np.exp(-0.8734633*a**5.4633574 - 0.12579775409572*np.sin(a)*np.cos(a**5.97746) - 0.360278500850849*np.cos(a)*np.cos(a**5.97746)) + 1.0*np.cos(a**0.8264235) + 26.011023)
    return x     
#v1 = lambda a: (-a*np.exp(-3.6822217*a**(-2.8971705) - 1.238104*a**3.7654412) + 0.046486337*a - 0.0993868964965362*a*np.exp(-a) + 0.29494765*a*np.exp(-3.6822217*a**(-2.8971705)))
#v2 = lambda a: (-0.02230581*(np.exp(a) + np.exp(np.cos((a**2)**0.95246226 - 1.3307008))*np.cos(3.6634598*a))*np.cos(2.0136378*a) + 0.052785624)
#T = lambda a: (-8.61150672305524*np.exp(-0.8734633*a**5.4633574 - 0.12579775409572*np.sin(a)*np.cos(a**5.97746) - 0.360278500850849*np.cos(a)*np.cos(a**5.97746)) + 1.0*np.cos(a**0.8264235) + 26.011023)

a = np.linspace(0.1, 2.8-0.01, 200)

fig_man, ax_man = plt.subplots(1)
fig_res, ax_res = plt.subplots(1)
for i in range(a.size):
    #print(i)
    p0 = np.array([x1(a[i]), x2(a[i]), v1(a[i]), v2(a[i])])
    p = solve_ivp(lambda t, p: odeCR3BP(t, p, mu),
                  t_span=(0, T(a[i])),
                  y0=p0,
                  method='LSODA',
                  t_eval = np.linspace(0, T(a[i]), 1000),
                  atol=1e-8,
                  rtol=1e-8)
    ax_man.plot(p.y[0,:], p.y[1,:])
    ax_res.plot(a[i], np.linalg.norm(p.y[:,-1] - p0), '.k')
plt.grid()
plt.show()