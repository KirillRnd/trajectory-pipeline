#!/usr/bin/env python
# coding: utf-8
import numpy as np

import pysr 
from pysr import PySRRegressor
from sympy.utilities.codegen import codegen


data = np.load('L1_Manifold_new_2.npy', allow_pickle=True)
obj = data.item() 
x1 = obj['x1']
v2 = obj['v2']
T = obj['T']
C = obj['C']
mu = obj['mu']

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


# %%
L1 =  0.836915131427382
L2 =  1.155682161024677
L3 = -1.005062645331442


#input_values = np.expand_dims(x1.flatten()-L1,-1)
N_points = 70
a = L1-x1
zeros_second = [0.02101619-0.001, 0.11879741+0.001]
#zeros_second = [0.02101619, 0.11879741]
idxes = np.logical_and(a>zeros_second[0],a<zeros_second[1])
#idxes = a>zeros_second[1]
x1_part = x1[idxes]
v2_part = v2[idxes]

input_values = np.expand_dims(L1-x1.flatten(),-1)
target_values = np.expand_dims(T.flatten(),-1)
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
    with open('L1_results_T.txt', 'a', encoding='utf-8') as f:
        f.write(f'{func_str} #{rmse_sci} #({np.min(input_values)},{np.max(input_values)})\n')