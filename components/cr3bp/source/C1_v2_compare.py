import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

mu = 3.0393890e-6

def v2(x0):
    return (
        np.sqrt((1 - mu) / (x0 + mu)) - (x0 + mu)
        + (0.47084948*x0
           + (x0 - 0.21319899)
           * (1.1044086*x0 / np.cos(0.24954179 - 2.0628507/np.log(x0)) - 0.0420995)
           * (np.sin(2.117359/np.log(x0)) + 0.014023513)
           / (x0 - 0.92994696)) * 1e-5
    )

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, "C:\\Users\\Anastasia\\Documents\\py\\pysr\\C1_adaptive_data.pickle"), "rb") as f:
    d = pickle.load(f)

x_true  = np.asarray(d["x"],  float)
vy_true = np.asarray(d["vy"], float)
order   = np.argsort(x_true)
x_true, vy_true = x_true[order], vy_true[order]

vy_pred = np.array([float(v2(x)) for x in x_true])
mask = np.isfinite(vy_pred)

fig, ax = plt.subplots(figsize=(10, 7))
ax.plot(x_true[mask], vy_true[mask],  lw=2.5, label="Истинное значение")
ax.plot(x_true[mask], vy_pred[mask], '--', lw=2.5, label="Аппроксимация")
ax.set_xlabel(r"$x$, безразм.", fontsize=14)
ax.set_ylabel(r"$v_y$, безразм.", fontsize=14)
ax.set_title(r"$v_y$: аппроксимация $v_2$ vs истинное значение ($C_1$)", fontsize=14)
ax.legend(fontsize=13)
ax.tick_params(labelsize=12)
ax.grid(True, ls="--", alpha=0.5)

ax_ins = ax.inset_axes([0.55, 0.25, 0.42, 0.38])
ax_ins.plot(x_true[mask], vy_pred[mask] - vy_true[mask], '-k', lw=1.5)
ax_ins.axhline(0, color='gray', lw=0.8)
ax_ins.set_title("Разница", fontsize=12)
ax_ins.set_xlabel(r"$x$, безразм.", fontsize=11)
ax_ins.set_ylabel(r"$\Delta$, безразм.", fontsize=11)
ax_ins.tick_params(labelsize=10)
ax_ins.grid(True, ls="--", alpha=0.4)

plt.tight_layout()
plt.savefig("C1_v2_compare.png", dpi=200)
plt.show()
