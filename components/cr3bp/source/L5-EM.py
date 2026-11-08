#!/usr/bin/env python
# coding: utf-8
import subprocess

result = subprocess.run(['rm', '-rf', '~/.julia/compiled', '~/.julia/artifacts', '~/.julia/loading-*'], capture_output=True, text=True)
print(result.stdout)

import numpy as np
import pandas as pd
df = pd.read_csv('EM_LP.csv', sep=';')
# Функция для проверки и преобразования строки в float (с заменой запятой на точку)
def convert_to_float(value):
    if type(value) == str:
        return float(value.replace(',', '.'))
    else:
        return value

for C in df.columns[:19]:
    df[C] = df[C].apply(lambda x: convert_to_float(x))


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

a=np.array(df['a'])
v1=np.array(df['v1'])
v2=np.array(df['v2'])
T=np.array(df['T'])

idxes = np.logical_and(a>1.06,a<1.72)
#idxes = a>2.74
a_part = a[idxes]
v1_part = v1[idxes]
v2_part = v2[idxes]
T_part = T[idxes]

input_values = np.expand_dims(a_part.flatten(),-1)
target_values = np.expand_dims(v1_part.flatten(),-1)
for i in range(3):
    print(i)
    model.fit(input_values, target_values,
            variable_names=["a"])
    
    
    # %%
    
    
    from sympy.utilities.lambdify import lambdastr
    from sympy.abc import a
    
    
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
    f = lambdastr(a, s)
    
    print(f)
    # 1. Научный формат (1e-07, 3e+00 и т.д.)
    rmse_sci = f'{RMSE:.1e}'          # или :.1e, :.2e – сколько цифр хотите
    rmse_sci = rmse_sci.replace('+', '')   # убираем «+» для «1e+00» → «1e00»
    
    # 2. Получаем строковое представление функции
    func_str = f.replace('\n', '')   # убираем возможный перевод строки
    
    # 3. Записываем «в конец»
    with open('L5_results_v1.txt', 'a', encoding='utf-8') as f:
        f.write(f'{func_str} #{rmse_sci} #({np.min(input_values)},{np.max(input_values)})\n')