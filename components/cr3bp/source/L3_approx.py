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

def v1_fun(x):
    return 0
def v2_fun(x):
    y = - (x + 1.0047855) * (1.8641998 - 0.10354004*math.cos(x**2)/x + 0.05944614206047/x**2 + 0.022025653372038/(x**2*math.cos(x + 0.46803632))) #4.5e-4
    return y
def T_fun(x):
    y = (math.log(-x + 184.123052928413*math.exp(math.sin(x + 1.3517317 - 1.3393477/x)**(-0.020119384)) + math.exp(math.cos(x**2 -3.9773538))))#9.7e-5
    return y
x_range = np.linspace(-1.99906, -1.00607, 100)

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
                  atol=1e-8,
                  rtol=1e-8)
    ax_man.plot(p.y[0,:], p.y[1,:])
    ax_res.plot(x_range[i], np.linalg.norm(p.y[:,-1] - p0), '.k')
plt.grid()
plt.show()