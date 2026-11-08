#!/usr/bin/env python
# coding: utf-8
# %%

# %%


import numpy as np


# %%


data = np.load('L2_Manifold_new.npy', allow_pickle=True)
obj = data.item() 
x1 = obj['x1']
v2 = obj['v2']
T = obj['T']
C = obj['C']
mu = obj['mu']


import numpy as np
import matplotlib.pyplot as plt
import pysr 
from pysr import PySRRegressor
from sympy.utilities.codegen import codegen


model = PySRRegressor(
        niterations=1000,  # < Increase me for better results
        binary_operators=["*", "+", "-","/","^"],
        unary_operators=[
            'exp',
            'cos',
            'sin',
            'log',
            'atan',
            #'sinh',
            #'cosh',
            #'asinh',
        ],
        constraints={'^': (-1, 1)},
        nested_constraints={"exp": {"exp": 0},
                            "^": {"^": 0},
                            "log": {"log": 0},
                            "atan": {"atan": 1},
                            #"asinh": {"sinh": 0,"cosh": 0, "asinh": 0},
                            #"sinh": {"sinh": 0,"cosh": 0, "asinh": 0},
                            #"cosh": {"sinh": 0,"cosh": 0, "asinh": 0},
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
#model.from_file(run_directory="outputs/20250725_195503_pJTlCg/")
#model.niterations = 10000
#model.warm_start = True
#"outputs/20250725_195503_pJTlCg/hall_of_fame.csv"

# %%
L1 =  0.836915131427382
L2 =  1.155682161024677
L3 = -1.005062645331442

a = x1-L2
zeros_second = [0.0394623 , 0.24305185, 0.28905999]
#idxes = np.logical_and(a>zeros_second[0]-0.001,a<zeros_second[1]+0.001)
idxes = a<4.34e-02
#idxes = a>(zeros_second[1]-0.001)
x1_part = x1[idxes]
v2_part = v2[idxes]

input_values = np.expand_dims(x1_part.flatten()-L2,-1)
target_values = np.expand_dims(v2_part.flatten(),-1)
for i in range(3):
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
    with open('L2_results_v2.txt', 'a', encoding='utf-8') as f:
        f.write(f'{func_str} #{rmse_sci} #({np.min(input_values)},{np.max(input_values)})\n')