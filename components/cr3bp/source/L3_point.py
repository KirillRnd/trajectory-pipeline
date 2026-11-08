#!/usr/bin/env python
# coding: utf-8
import subprocess

result = subprocess.run(['rm', '-rf', '~/.julia/compiled', '~/.julia/artifacts', '~/.julia/loading-*'], capture_output=True, text=True)
print(result.stdout)


import numpy as np

import pysr 
from pysr import PySRRegressor
from sympy.utilities.codegen import codegen


import numpy as np
from   scipy.optimize import root_scalar

# ---------- функция f(x; μ) = ∂Ω/∂x для y = 0 -------------------------------
def dOmega_dx(x, mu):
    """
    Первая производная эффективного потенциала CR3BP по x
    для коллинеарных точек (y = 0).
    """
    r1 = np.abs(x + mu)          # расстояние до m1
    r2 = np.abs(x - 1 + mu)      # расстояние до m2
    return x - (1 - mu)*(x + mu)/r1**3 - mu*(x - 1 + mu)/r2**3


# ---------- поиск L1, L2, L3 для одного значения μ --------------------------
def collinear_L_points(mu, tol=1e-12):
    f = lambda x: dOmega_dx(x, mu)

    # ---- L1 (между примариями, ближе к m2) ----------------------------------
    b = 1.0 - mu - 1e-12          # чуть левее второй примарии
    a = b - 0.8                   # начальная левая граница
    while f(a)*f(b) > 0:          # расширяем, пока не появится смена знака
        a -= 0.5
    L1 = root_scalar(f, bracket=(a, b), method='brentq',
                     xtol=tol, rtol=tol).root

    # ---- L2 (снаружи m2, x > 1-μ) -------------------------------------------
    a = 1.0 - mu + 1e-12          # чуть правее второй примарии
    b = a + 1.0
    while f(a)*f(b) > 0:
        b += 1.0
    L2 = root_scalar(f, bracket=(a, b), method='brentq',
                     xtol=tol, rtol=tol).root

    # ---- L3 (слева от m1, x < –μ) -------------------------------------------
    b = -mu - 1e-12               # чуть левее первой примарии
    a = b - 1.0
    while f(a)*f(b) > 0:
        a -= 1.0
    L3 = root_scalar(f, bracket=(a, b), method='brentq',
                     xtol=tol, rtol=tol).root

    return L1, L2, L3


# ---------- массивы значений -------------------------------------------------
N_uniform = 500
N_exp     = 100

mu_uniform = np.linspace(0.0, 0.5, N_uniform)
mu_exp     = np.geomspace(1e-10, mu_uniform[1], N_exp)   # ~[10⁻⁸, 1e-3]

mu_arr = np.unique(np.concatenate(([0.0], mu_exp, mu_uniform)))
M      = mu_arr.size                                    # общее число точек

L1_arr = np.empty(M)
L2_arr = np.empty(M)
L3_arr = np.empty(M)

for i, mu in enumerate(mu_arr):
    # μ = 0 даёт аналитические решения, чтобы не сталкиваться с 0/0
    if np.isclose(mu, 0.0, rtol=1e-12, atol=1e-12):
        L1_arr[i] =  1.0     # x = +1
        L2_arr[i] =  1.0
        L3_arr[i] = -1.0     # x = –1
        continue

    # остальные случаи – численное решение
    L1_arr[i], L2_arr[i], L3_arr[i] = collinear_L_points(mu)

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

input_values = np.expand_dims(mu_arr.flatten(),-1)
target_values = np.expand_dims(L3_arr.flatten(),-1)
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
    with open('L3_point_results.txt', 'a', encoding='utf-8') as f:
        f.write(f'{func_str} #{rmse_sci} #({np.min(input_values)},{np.max(input_values)})\n')