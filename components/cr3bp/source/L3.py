#!/usr/bin/env python
# coding: utf-8
# %%

# %%


import numpy as np


# %%


data = np.load('L3_Manifold.npy', allow_pickle=True)
obj = data.item() 
x1 = obj['x1']
v2 = obj['v2']
T = obj['T']
C = obj['C']
mu = obj['mu']


# %%


import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
import pysr 
from pysr import PySRRegressor
from scipy.optimize import least_squares
from sympy.utilities.codegen import codegen


model = PySRRegressor(
        niterations=2000,  # < Increase me for better results
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


input_values = np.expand_dims(x1.flatten(),-1)
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
