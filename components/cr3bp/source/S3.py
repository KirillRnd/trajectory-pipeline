#!/usr/bin/env python
# coding: utf-8
# %%

# %%


import numpy as np


# %%
import pandas as pd
import glob
import os

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
mu = mu_list[1]
df_SP_mu = df_SP[df_SP['mu'] == mu]

a = np.array(df_SP_mu['a'])
x1 = np.array(df_SP_mu['x1'])
x2 = np.array(df_SP_mu['x2'])
v1 = np.array(df_SP_mu['v1'])
v2 = np.array(df_SP_mu['v2'])
T = np.array(df_SP_mu['T'])


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
            'atan'
        ],
        constraints={'^': (-1, 1)},
        nested_constraints={"exp": {"exp": 0},
                            "^": {"^": 0},
                            "log": {"log": 0},
                            "atan": {"cos": 1,"sin": 1, "exp": -1, "atan": 0},
                            "cos": {"cos": 0,"sin": 0, "exp": 0, "atan": 1},
                            "sin": {"cos": 0,"sin": 0, "exp": 0, "atan": 1}
                           },
        populations=36,
        verbosity=1,
        maxsize=45,
        warm_start = False,
        #warmup_maxsize_by = 0.1,
        #parsimony = 1e-10
    )


input_values = np.expand_dims(a.flatten(),-1)
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
# 1. Научный формат (1e-07, 3e+00 и т.д.)
rmse_sci = f'{RMSE:.1e}'          # или :.1e, :.2e – сколько цифр хотите
rmse_sci = rmse_sci.replace('+', '')   # убираем «+» для «1e+00» → «1e00»

# 2. Получаем строковое представление функции
func_str = f.replace('\n', '')   # убираем возможный перевод строки

# 3. Записываем «в конец»
with open('S3_results_T.txt', 'a', encoding='utf-8') as f:
    f.write(f'{func_str} #{rmse_sci}\n')