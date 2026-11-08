#!/usr/bin/env python
# coding: utf-8
import numpy as np

import pysr 
from pysr import PySRRegressor
from sympy.utilities.codegen import codegen
import pandas as pd

df_L1 = pd.read_csv('halo/L1_halo.csv')
x1 = np.array(df_L1['x'])
x3 = np.array(df_L1['z'])
v2 = np.array(df_L1['vy'])
T = np.array(df_L1['T'])
mu = 2.447832293839728e-06

model = PySRRegressor(
        niterations=3000,  # < Increase me for better results
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
                            "atan": {"atan": 0},
                            #"tanh": {"cos": 1,"sin": 1,  "tanh": 1},
                            "cos": {"cos": 0,"sin": 0},
                            "sin": {"cos": 0,"sin": 0}
                           },
        populations=36,
        verbosity=1,
        maxsize=35,
        warm_start = False,
        warmup_maxsize_by = 0.05,
        #parsimony = 1e-10
    )

for i in range(10):
    input_values = np.expand_dims(x1.flatten(),-1)
    target_values = np.expand_dims(x3.flatten(),-1)
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
    with open('L1-Halo_results_z.txt', 'a', encoding='utf-8') as f:
        f.write(f'{func_str} #{rmse_sci} #({np.min(input_values)},{np.max(input_values)})\n')