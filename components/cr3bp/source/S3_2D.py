#!/usr/bin/env python
# coding: utf-8
import subprocess

result = subprocess.run(['rm', '-rf', '~/.julia/compiled', '~/.julia/artifacts', '~/.julia/loading-*'], capture_output=True, text=True)
print(result.stdout)


import numpy as np


# %%
import pandas as pd
import glob
import os
from scipy.interpolate import CubicSpline

# ---- Параметры -------------------------------------------------------------
FOLDER_WITH_EXCEL = r"./LP_SP"    # папка, где лежат .xlsx
PATTERN = "*.xlsx"                      # при необходимости можно изменить на *.xlsm и т.д.
ADD_SOURCE_COLUMNS = True               # добавить колонки с именем файла/листа
# ---------------------------------------------------------------------------

def read_all_excels(folder, pattern="*.xlsx", add_source_cols=True):
    """
    Читать все Excel-файлы из папки и вернуть один объединённый DataFrame.

    :param folder: Папка с .xlsx
    :param pattern: Глоб-шаблон для поиска файлов
    :param add_source_cols: Добавлять ли столбцы __file__ и __sheet__
    """
    full_pattern = os.path.join(folder, pattern)
    files = glob.glob(full_pattern)

    if not files:
        raise FileNotFoundError(f"По шаблону {full_pattern!r} ничего не найдено")

    frames = []  # сюда будем складывать все DataFrame'ы

    for fname in files:
        # Читаем сразу все листы: вернётся словарь {имя_листа: DataFrame}
        sheets_dict = pd.read_excel(fname, sheet_name=None, engine="openpyxl")

        for sheet_name, df in sheets_dict.items():
            if add_source_cols:
                df = df.copy()  # чтобы не трогать оригинал
                df["file"]  = os.path.basename(fname)
                df["sheet"] = sheet_name
            frames.append(df)

    # Объединяем
    combined = pd.concat(frames, ignore_index=True)
    return combined

df_all = read_all_excels(FOLDER_WITH_EXCEL)
df_all['mu'] = [float(x.replace('.xlsx','').replace('mu=','')) for x in df_all['file']]
df_SP = df_all[df_all['sheet'] == 'SP']

mu_list = list(set(df_SP['mu']))
mu_list.sort()
mu_list = np.array(mu_list)
v1_list = []
v2_list = []
T_list = []
df_SP_mu = df_SP[df_SP['mu'] == mu_list[0]]
a_etalon = np.array(df_SP_mu['a'])
for mu in mu_list:
    df_SP_mu = df_SP[df_SP['mu'] == mu]
    
    cs = CubicSpline(np.array(df_SP_mu['a']), np.array(df_SP_mu['v1']))
    v1_corrected = cs(a_etalon)
    v1_list.append(v1_corrected)
    
    cs = CubicSpline(np.array(df_SP_mu['a']), np.array(df_SP_mu['v2']))
    v2_corrected = cs(a_etalon)
    v2_list.append(v2_corrected)
    
    cs = CubicSpline(np.array(df_SP_mu['a']), np.array(df_SP_mu['T']))
    T_corrected = cs(a_etalon)
    T_list.append(T_corrected)
v1 = np.array(v1_list)
v2 = np.array(v2_list)
T = np.array(T_list)

a = np.tile(a_etalon, (v1.shape[0], 1))
mu = np.tile(mu_list, (v1.shape[1], 1)).T
'''
import numpy as np
m = mu
x = a
n_m, n_x = v2.shape
k = 500                       # целевой размер
dm = np.mean(np.diff(m[:, 0]))
dx = np.mean(np.diff(x[0]))
# «важность» = норма градиента (можно заменить на кривизну, ошибку и т.д.)
dv_dm, dv_dx = np.gradient(T, dm, dx)
imp = np.hypot(dv_dm, dv_dx)          # (10, 838), ненулевая и положительная
imp = (imp - imp.min()) / (imp.ptp() + 1e-12) + 1e-3    # нормировка 0…1

# Этот способ работает
r_min = np.hypot(n_m, n_x) / np.sqrt(k * np.pi)   # эмпирически ~равномерно

# 1) генерация много-много (3–5k) кандидатов с весами
n_cand = 5 * k
flat = np.random.choice(n_m*n_x, n_cand, replace=False, p=imp.ravel()/imp.sum())
cands = np.column_stack(np.unravel_index(flat, v2.shape)).astype(float)

# 2) Poisson-disk фильтр (O(k^2), здесь маленькие n, поэтому ок)
chosen = []
for p in cands:
    if all(np.linalg.norm(p - q) >= r_min for q in chosen):
        chosen.append(tuple(p.astype(int)))
    if len(chosen) == k:
        break
# если не набрали 500, слегка уменьшаем r_min и продолжаем
while len(chosen) < k:
    r_min *= 0.9
    for p in cands:
        if all(np.linalg.norm(p - q) >= r_min for q in chosen):
            chosen.append(tuple(p.astype(int)))
        if len(chosen) == k:
            break

i_sel, j_sel = map(np.array, zip(*chosen))

#v2_sub = v2[i_sel, j_sel]
T_sub = T[i_sel, j_sel]
a_sub = a[i_sel, j_sel]
mu_sub = mu[i_sel, j_sel]
'''
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
            'atan',
        ],
        #extra_sympy_mappings={"pimult": lambda x: np.pi*x},
        #nested_constraints={"cos": {"cos": 0, "sin": 0},"sin": {"cos": 0, "sin": 0}},
        constraints={'^': (-1, 1)},
        #nested_constraints={"exp": {"exp": 0}},
        #nested_constraints={"exp": {"exp": 0},"log": {"log": 0}},
        #nested_constraints={"^": {"^": 0},"log": {"log": 0},"cos":{"cos": 0,"sin": 0,"log": 0},"sin":{"cos": 0,"sin": 0,"log": 0}},
        nested_constraints={"exp": {"exp": 0}, 
                            "^": {"^": 0},
                            "cos":{"cos": 0,"sin": 0},
                            "sin":{"cos": 0,"sin": 0},
                            "atan": {"atan": 0}, 
                           },                
        populations=36,
        verbosity=1,
        maxsize=30,
        #batching=True,
        warm_start = False,
        #denoise=True
    )

#a = np.array(df_SP['a'])
#mu = np.array(df_SP['mu'])
#v2 = np.array(df_SP['v2'])
input_values_2d = np.array([a.flatten(),mu.flatten()]).T
target_values = np.expand_dims(v2.flatten(),-1)
model.fit(input_values_2d, target_values, 
        variable_names=["a", "m"])


# %%


from sympy.utilities.lambdify import lambdastr
from sympy.abc import a, m


# %%


N=None

test_preds = model.predict(input_values_2d,N)
test_trues = target_values.reshape(test_preds.shape)
MSE = np.square(np.subtract(test_trues,test_preds)).mean() 
s = model.sympy(N).simplify()
#display(s)
RMSE = np.sqrt(MSE)
print(RMSE)

print('Python Code:')
f = lambdastr((a, m), s)

print(f)
# 1. Научный формат (1e-07, 3e+00 и т.д.)
rmse_sci = f'{RMSE:.1e}'          # или :.1e, :.2e – сколько цифр хотите
rmse_sci = rmse_sci.replace('+', '')   # убираем «+» для «1e+00» → «1e00»

# 2. Получаем строковое представление функции
func_str = f.replace('\n', '')   # убираем возможный перевод строки

# 3. Записываем «в конец»
with open('S3_results_v2.txt', 'a', encoding='utf-8') as f:
    f.write(f'{func_str} #{rmse_sci}\n')
