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

mu = 0.012150584460351
x1_fun = lambda x: x
x2_fun = lambda x: 0

L2 =  1.155682161024677

def v1_fun(x):
    return 0
def v2_fun(x):
    x = x - L2
    if x>=0 and x<0.0394623:
        y = (x*math.exp((x*(x*(math.cos(0.44315043/(x - 0.0712678)) + 2.062117) + 0.46996135))**x)/(4*x - 0.49699014)) #3.0e-05 #(9.999999999998899e-05,0.040894726030323625)

    elif x>=0.0394623 and x<0.24305185:
        y = ((-1.46250174055988*x**3 - 0.35126773*x*(x + 2.807831e-5*math.exp(math.sin((0.38976994*x - 0.7654842)/x)) + 0.013415855) + 9.8630042159363e-6*math.exp(math.sin(0.33920822/x)) + 0.000373935844532679)/x**2) #3.4e-05
    elif x>=0.24305185:
        y = (-1.4388031*x - math.cos(x**2*(1.4388031*math.atan(x) + 0.3300813)*math.atan((x - 0.3300813)*(0.9308737*math.atan(x) + 1.79023032846377)*math.log(x))) + 0.6302827) #1.1e-07
    return y
def T_fun(x):
    x = x - L2
    y = (1.0*x + 0.40856314*math.tanh(math.tanh(1.9805193 - 0.11379527/x)) + 3.683467 + 7.02544599473763*math.exp(-0.17211303/math.tanh(x))) #2.8e-03
    return y
    
x_range = L2+np.linspace(1e-4, 0.3464867, 200)

fig_man, ax_man = plt.subplots(1)
fig_res, ax_res = plt.subplots(1)
for i in range(x_range.size):
    #print(i)
    p0 = np.array([x1_fun(x_range[i]), x2_fun(x_range[i]), v1_fun(x_range[i]), v2_fun(x_range[i])])
    p = solve_ivp(lambda t, p: odeCR3BP(t, p, mu),
                  t_span=(0, T_fun(x_range[i])),
                  y0=p0,
                  method='LSODA',
                  t_eval = np.linspace(0, T_fun(x_range[i]), 1000),
                  atol=1e-12,
                  rtol=1e-12)
    ax_man.plot(p.y[0,:], p.y[1,:])
    ax_res.plot(x_range[i], np.linalg.norm(p.y[:,-1] - p0), '.k')
plt.grid()
plt.show()