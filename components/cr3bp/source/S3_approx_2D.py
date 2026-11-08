#Аппроксимация всего семейства короткопериодических орбит (оно же S3)
import numpy as np
from matplotlib import pyplot as plt
from scipy.integrate import solve_ivp

def odeCR3BP(t, p, mu):
    R = np.sqrt((p[0] + mu)**2 + p[1]**2)
    r = np.sqrt((p[0] - 1 + mu)**2 + p[1]**2)
    dpdt = np.array([p[2], p[3],
    2 * p[3] + p[0] - (1 - mu) * (p[0] + mu) / R**3 - mu * (p[0] - 1 + mu) / r**3,
    -2 * p[2] + p[1] - (1 - mu) * p[1] / R**3 - mu * p[1] / r**3])

    return dpdt

#Земля-Луна
mu0 = 0.012150584460351

#Солнце-Земля
#mu0 = 3.0035e-6

def x1_fun(a, mu):
    y = (-mu + np.sin(a + np.pi*5/6))
    return y
def x2_fun(a, mu):
    y = (np.sin(a - np.pi*2/3))
    return y
def v1_fun(a, mu):
    y = (-a*((mu*np.cos(0.22937126**a - np.log(a)) - 0.41244736*np.cos(0.22130254**a + np.log(a)))*np.sin(a + 0.028886221) + 0.26014933*np.cos(1.2741468*a + 5.4069505))) #1.1e-03
    return y
def v2_fun(a, mu):
    y = (a*(-6.557952*mu + 0.26311928*np.exp(1.4665749*a) + 0.415885222275072)*np.exp(-1.4665749*a)*np.cos(0.5028553*a*mu - a + 0.93205124)) #2.7e-03
    return y
def T_fun(a, mu):
    y = (mu*(4.928138*np.cos(a - 0.6908796) + 2.9778968732458 + 43.95868/(np.exp(a) + np.sin(88.58396*mu)))*np.cos(np.exp(-83.87106*mu)) + 6.283895) #1.1e-02
    return y
    
x_range = np.linspace(0.005, 4.19, 30)

fig_man, ax_man = plt.subplots(1)
fig_res, ax_res = plt.subplots(1)
err_list = []
for i in range(x_range.size):
    p0 = np.array([x1_fun(x_range[i], mu0), x2_fun(x_range[i], mu0), v1_fun(x_range[i], mu0), v2_fun(x_range[i], mu0)])
    p = solve_ivp(lambda t, p: odeCR3BP(t, p, mu0),
                  t_span=(0, T_fun(x_range[i], mu0)),
                  y0=p0,
                  method='LSODA',
                  t_eval = np.linspace(0, T_fun(x_range[i], mu0), 1000),
                  atol=1e-12,
                  rtol=1e-12)
    ax_man.plot(p.y[0,:], p.y[1,:])
    err = np.linalg.norm(p.y[:,-1] - p0)
    ax_res.plot(x_range[i], err, '.k')
ax_man.axis('equal')
ax_res.grid()