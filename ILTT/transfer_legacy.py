#!/usr/bin/env python
import argparse
import time

import ILTTToolbox
from scipy.optimize import root
import matplotlib.pyplot as plt
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(
        description="Межпланетный перелёт с электрореактивной тягой (Земля–Марс по умолчанию)."
    )

    parser.add_argument("--year", type=int, default=2026, help="Год старта (по умолчанию 2026)")
    parser.add_argument("--month", type=int, default=1, help="Месяц старта (по умолчанию 1)")
    parser.add_argument("--day", type=int, default=1, help="День старта (по умолчанию 1)")

    parser.add_argument("--power", type=float, default=1350,
                        help="Мощность ЭРДУ, Вт (по умолчанию 1350)")
    parser.add_argument("--mass", type=float, default=367,
                        help="Полная масса КА, кг (по умолчанию 367)")
    parser.add_argument("--eta", type=float, default=0.45,
                        help="КПД ЭРДУ (по умолчанию 0.45)")

    parser.add_argument("--planet-start", type=str, default="Earth",
                        help="Планета старта (по умолчанию Earth)")
    parser.add_argument("--planet-end", type=str, default="Mars",
                        help="Планета назначения: Mars, Venus и т.п. (по умолчанию Mars)")

    return parser.parse_args()


def main():
    args = parse_args()

    # ВХОДНЫЕ ПАРАМЕТРЫ
    t_start = ILTTToolbox.juliandate(args.year, args.month, args.day)
    N = args.power
    m0 = args.mass
    eta = args.eta
    planet_start = args.planet_start
    planet_end = args.planet_end

    t_begin = time.perf_counter()

    # ОСНОВНОЙ КОД (почти как у вас)
    ae = 149597870.700  # км
    mug = 132712.43994e6  # км^3/с^2

    # орбитальный период Земли
    T_earth = 2 * np.pi * np.sqrt(np.power(ae, 3) / mug)

    # коэффициенты обезразмеривания
    r_unit = ae
    V_unit = np.sqrt(mug / ae)
    T_unit = T_earth / (2 * np.pi)

    end_pos, end_vel = ILTTToolbox.planet_model_simple(
        t_start, planet_end, dimensionless=True
    )
    [a, eMag, i, O, o, nu, truLon, argLat, lonPer, p] = ILTTToolbox.rv2orb(
        end_pos.T, end_vel.T, 1
    )
    Omega_end = O
    omega_end = lonPer
    i_end = i
    e_end = eMag
    kappa = a[0]

    # ещё раз T_unit, как в исходном коде
    T_earth = 2 * np.pi * np.sqrt(np.power(ae, 3) / mug)
    T_unit = T_earth / (2 * np.pi)

    r0, v0 = ILTTToolbox.planet_model_simple(
        t_start, planet_start, dimensionless=True
    )

    i_target = i_end[0]
    O_target = Omega_end[0]
    e_target = e_end[0]
    o_target = omega_end[0]
    a_target = kappa

    phi_syn = ILTTToolbox.calculate_phi_syn(t_start, planet_start, planet_end)
    OM = phi_syn / (2 * np.pi)

    lmbd_initial, k_best = ILTTToolbox.find_min_positive_lmbd(
        OM, a[0], ILTTToolbox.a_OM, max_abs_k=5
    )
    t0 = 0
    d = 1
    F, x_initial = ILTTToolbox.make_F_function(
        r0, v0, lmbd_initial, kappa, t0, d, i_target, O_target, e_target, o_target
    )
    loss = ILTTToolbox.create_loss_fuction(F, t_start, planet_end)
    res = root(loss, x_initial, method="hybr")

    result_dict = F(res.x)
    traj = result_dict["traj"]
    mass_consumption = ILTTToolbox.m_p(result_dict["Jf"], m0, eta, N)
    end_pos, end_vel = ILTTToolbox.planet_model_simple(
        t_start + result_dict["T_days"], planet_end, dimensionless=True
    )

    res_r = np.linalg.norm(end_pos[0] - result_dict["rf"])
    res_v = np.linalg.norm(end_vel[0] - result_dict["vf"])

    orbit_start, _ = ILTTToolbox.planet_model_simple(
        t_start + np.linspace(0, 366, 100), planet_start, dimensionless=True
    )
    orbit_end, _ = ILTTToolbox.planet_model_simple(
        t_start + np.linspace(0, 687, 100), planet_end, dimensionless=True
    )

    # ГРАФИК
    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection="3d")

    print("Продолжительность перелёта", round(result_dict["T_days"]), "суток")
    print("Требуемый запас ксенона", np.round(mass_consumption, 1), "кг")
    print("Норма ошибки по положению:", res_r)
    print("Норма ошибки по скорости:", res_v)

    # Орбиты и траектория
    ax.plot(*orbit_start.T, color="steelblue", label="Орбита Земли")
    ax.plot(*orbit_end.T, color="crimson", label=f"Орбита {planet_end}")
    ax.plot(*traj.T, color="black", label="Траектория")
    ax.scatter(*end_pos.T, color="crimson", label=planet_end)
    ax.scatter(*result_dict["rf"].T, color="black", label="КА в конце перелёта")

    # Подписи осей и легенда
    ax.set_xlabel("x (а.е.)")
    ax.set_ylabel("y (а.е.)")
    ax.set_zlabel("z (а.е.)")
    ax.set_title(f"Перелёт {planet_start} → {planet_end}")
    ax.legend()

    plt.tight_layout()

    t_end = time.perf_counter()
    print(f"Время работы программы: {t_end - t_begin:.2f} с")

    plt.show()


if __name__ == "__main__":
    main()
