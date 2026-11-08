#!/usr/bin/env python
# coding: utf-8
# %%
import subprocess

result = subprocess.run(['rm', '-rf', '~/.julia/compiled', '~/.julia/artifacts', '~/.julia/loading-*'], capture_output=True, text=True)
print(result.stdout)



import numpy as np


# %%


data = np.load('D1_Manifold_new.npy', allow_pickle=True)
obj = data.item() 
x1 = obj['x1']
v2 = obj['v2']
T = obj['T']
C = obj['C']
mu = obj['mu']


# %%

def odeCR3BP(t, p, mu):
    R = np.sqrt((p[0] + mu)**2 + p[1]**2)
    r = np.sqrt((p[0] - 1 + mu)**2 + p[1]**2)
    dpdt = np.array([p[2], p[3],
    2 * p[3] + p[0] - (1 - mu) * (p[0] + mu) / R**3 - mu * (p[0] - 1 + mu) / r**3,
    -2 * p[2] + p[1] - (1 - mu) * p[1] / R**3 - mu * p[1] / r**3])

    return dpdt
    
import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
import pysr 
from pysr import PySRRegressor
from scipy.optimize import least_squares
from sympy.utilities.codegen import codegen
from scipy.integrate import solve_ivp

res_list = []
for i in range(x1.size):
    p0 = np.array([x1[i], 0, 0, v2[i]])
    p = solve_ivp(lambda t, p: odeCR3BP(t, p, mu),
                  t_span=(0, T[i]),
                  y0=p0,
                  method='LSODA',
                  t_eval = np.linspace(0, T[i], 1000),
                  atol=1e-12,
                  rtol=1e-12)
    res = np.linalg.norm(p.y[:,-1] - p0)
    res_list.append(res)
weights = np.array(res_list)
weights_norm = (1/weights)/np.max(1/weights)
    
model = PySRRegressor(
        niterations=1000,  # < Increase me for better results
        binary_operators=["*", "+", "-","/","^"],
        unary_operators=[
            'exp',
            'cos',
            'sin',
            'log',
            'atan',
            #'tanh',
        ],
        constraints={'^': (-1, 1)},
        nested_constraints={"exp": {"exp": 0},
                            "^": {"^": 0},
                            "log": {"log": 0},
                            "atan": {"atan": 1},
                            #"tanh": {"cos": 1,"sin": 1,  "tanh": 1},
                            "cos": {"cos": 0,"sin": 0},
                            "sin": {"cos": 0,"sin": 0}
                           },
        populations=36,
        verbosity=1,
        maxsize=35,
        warm_start = False,
        #warmup_maxsize_by = 0.1,
        #parsimony = 1e-10
    )

zeros_first = 0.77609249
# %%
L1 =  0.836915131427382
L2 =  1.155682161024677
L3 = -1.005062645331442

idxes = x1>0.73
x1_part = x1[idxes]
v2_part = v2[idxes]

input_values = np.expand_dims(x1_part.flatten(),-1)
target_values = np.expand_dims(v2_part.flatten(),-1)
for i in range(10):
    print(i)
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
    # 1. Научный формат (1e-07, 3e+00 и т.д.)
    rmse_sci = f'{RMSE:.1e}'          # или :.1e, :.2e – сколько цифр хотите
    rmse_sci = rmse_sci.replace('+', '')   # убираем «+» для «1e+00» → «1e00»
    
    # 2. Получаем строковое представление функции
    func_str = f.replace('\n', '')   # убираем возможный перевод строки
    
    # 3. Записываем «в конец»
    with open('D1_results_v2.txt', 'a', encoding='utf-8') as f:
        f.write(f'{func_str} #{rmse_sci} #({np.min(input_values)},{np.max(input_values)})\n')