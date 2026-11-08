#!/usr/bin/env python
# coding: utf-8
# %%


import numpy as np



data = np.load('L1_Manifold.npy', allow_pickle=True)
obj = data.item() 
x1 = obj['x1']
v2 = obj['v2']
T = obj['T']
C = obj['C']
mu = obj['mu']


import numpy as np
from scipy.integrate import solve_ivp
import math

def odeCR3BP(t, p, mu):
    R = np.sqrt((p[0] + mu)**2 + p[1]**2)
    r = np.sqrt((p[0] - 1 + mu)**2 + p[1]**2)
    dpdt = np.array([p[2], p[3],
    2 * p[3] + p[0] - (1 - mu) * (p[0] + mu) / R**3 - mu * (p[0] - 1 + mu) / r**3,
    -2 * p[2] + p[1] - (1 - mu) * p[1] / R**3 - mu * p[1] / r**3])

    return dpdt

x1_new = []
v2_new = []
for i in range(len(x1)):
    #print(i)
    p0 = np.array([x1[i], 0, 0, v2[i]])
    p = solve_ivp(lambda t, p: odeCR3BP(t, p, mu),
                  t_span=(0, T[i]/2),
                  y0=p0,
                  method='LSODA',
                  t_eval = np.linspace(0, T[i]/2, 1000),
                  atol=1e-12,
                  rtol=1e-12)
    x1_new.append(p.y[0,-1])
    v2_new.append(p.y[3,-1])


# %%
x1_new_arr = np.array(x1_new)
v2_new_arr = np.array(v2_new)

# %%
L1 =  0.836915131427382
L2 =  1.155682161024677
L3 = -1.005062645331442

# %%


import scipy.io as sio
import numpy as np
import pysr 
from pysr import PySRRegressor
from scipy.optimize import least_squares
from sympy.utilities.codegen import codegen


model = PySRRegressor(
        niterations=1000,  # < Increase me for better results
        binary_operators=["*", "+", "-","/","^"],
        unary_operators=[
            'exp',
            'cos',
            'sin',
            'log',
        ],
        #extra_sympy_mappings={"pimult": lambda x: np.pi*x},
        #nested_constraints={"cos": {"cos": 0, "sin": 0},"sin": {"cos": 0, "sin": 0}},
        constraints={'^': (-1, 1)},
        #nested_constraints={"exp": {"exp": 0}},
        #nested_constraints={"exp": {"exp": 0},"log": {"log": 0}},
        #nested_constraints={"^": {"^": 0},"log": {"log": 0},"cos":{"cos": 0,"sin": 0,"log": 0},"sin":{"cos": 0,"sin": 0,"log": 0}},
        nested_constraints={"exp": {"exp": 0}, "^": {"^": 0},"log": {"log": 0},"cos":{"cos": 0,"sin": 0, "exp": 0,"log": 0},"sin":{"cos": 0,"sin": 0,"exp": 0,"log": 0}},
        populations=36,
        verbosity=1,
        maxsize=35,
        #batching=True,
        warm_start = False,
        #denoise=True
    )


# %%


input_values = np.expand_dims(x1_new_arr.flatten()-L1,-1)
target_values = np.expand_dims(T.flatten(),-1)
model.fit(input_values, target_values,
        variable_names=["x"])


# %%


from sympy.utilities.lambdify import lambdastr
from sympy.abc import x


# %%


N=None

test_preds = model.predict(input_values,N)
test_trues = target_values.reshape(test_preds.shape)
MSE = np.square(np.subtract(test_trues,test_preds)).mean() 
s = model.sympy(N).simplify()
#display(s)
RMSE = np.sqrt(MSE)
print(RMSE)

print('Python Code:')
f = lambdastr(x, s)

print(f)
