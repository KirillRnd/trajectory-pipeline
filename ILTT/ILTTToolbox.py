#!/usr/bin/env python
# coding: utf-8
import math
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import datetime

def calculate_R_matrix(r0, v0):
    """
    Calculate a rotation matrix from two vectors.
    Args:
        r0: ndarray, shape (3,)
        v0: ndarray, shape (3,)
    Returns:
        R: ndarray, shape (3,3)
    """
    e1 = np.asarray(r0)
    e2 = np.asarray(v0)
    e3 = np.cross(e1, e2)
    R = np.vstack([e1, e2, e3])
    return R

def calculate_phi_syn(t_start, planet_start, planet_end):
    end_pos, end_vel = planet_model_simple(t_start, planet_end,dimensionless=True)
    [a,eMag,i,O,o,nu,truLon,argLat,lonPer,p] = rv2orb(end_pos.T,end_vel.T,1)
    
    start_pos, start_vel = planet_model_simple(t_start, planet_start,dimensionless=True)
    # Элементы Земли в момент t_start
    a_E, e_E, i_E, O_E, o_E, nu_E, truLon_E, argLat_E, lonPer_E, p_E = rv2orb(start_pos.T, start_vel.T, 1)
    
    # Истинные долготы (если truLon не определён, используем Ω+ω+ν)
    lam_E = np.where(np.isfinite(truLon_E), truLon_E, O_E + o_E + nu_E)
    lam_M = np.where(np.isfinite(truLon),   truLon,   O   + o   + nu)
    
    # Синодическая фаза Марс–Земля при t_start: φ = λ_M - λ_E, приведённая к (−π, π]
    phi_syn = np.arctan2(np.sin(lam_M - lam_E), np.cos(lam_M - lam_E))   # рад
    return phi_syn

def calculate_dm_for_Reo_matrix(k, omega_target, e_target):
    C_ecc_0 = (k-1) * 3.272584669562773
    C_ecc_1 = (k-1) * -1.9315126322573586
    C_ecc_2 = (k-1) * -0.4543650380418002
    C_ecc = C_ecc_0 + np.sin(omega_target) * (
        C_ecc_1 * np.sin(omega_target) + 
        C_ecc_2 * np.sin(3 * omega_target)
    )
    dm = -e_target / C_ecc
    return dm

def calculate_j_for_RiO_matrix(k, Omega_target, i_target):
    Ci0 = (k * (0.12653741 - 0.022551617 * k) * (k + 0.8123615) - 0.18755639)
    Ci1 = 0.0012084354 * (k - 1.4255633) * (k**3 - 0.99985284)
    delta_i_coef = Ci0 + Ci1 * np.cos(2 * Omega_target)

    if i_target == 0:
        j = 0.0
    else:
        j = -i_target / delta_i_coef
    return j

def calculate_Reo_matrix_noapprox(dm, omega_target):
    theta = 0.642
    
    dmax = 0.999 * abs(np.sin(theta))   # чуть меньше, чтобы не попасть на ноль
    dm_clipped = np.clip(dm, -dmax, dmax)
    
    m = -np.sin(theta) + dm_clipped  # X_rotated
    n = np.cos(theta)        # Y_rotated

    e_param = m * np.cos(theta) + n * np.sin(theta)
    a_param = -m * np.sin(theta) + n * np.cos(theta)

    denom = a_param * (1 - e_param ** 2)
    R_e = np.array([
        [a_param * (1 - e_param), 0, 0],
        [0, (1 + e_param) / np.sqrt(denom), 0],
        [0, 0, (1 + e_param) / np.sqrt(denom) * a_param * (1 - e_param)]
    ])

    o_input = omega_target / 2 + (1/6) * np.sin(2 * omega_target) + (1/32) * np.sin(4 * omega_target)

    R_rot = np.array([
        [np.cos(o_input), -np.sin(o_input), 0],
        [np.sin(o_input),  np.cos(o_input), 0],
        [0,               0,               1]
    ])

    R_eo = R_rot @ R_e @ R_rot.T
    
    return R_eo

def calculate_RiO_matrix_noapprox(j, Omega_target):
    R_i = np.array([
        [1, 0, 0],
        [0, 1/(1+j**2), -j/(1+j**2)],
        [0, j/(1+j**2), 1/(1+j**2)]
    ])

    R_rot = np.array([
        [np.cos(Omega_target), -np.sin(Omega_target), 0],
        [np.sin(Omega_target),  np.cos(Omega_target), 0],
        [0,                    0,                   1]
    ])

    R_iO = R_rot @ R_i @ R_rot.T
    return R_iO

def calculate_Reo_matrix(k, e_target, omega_target):
    """
    Calculate R_eo matrix.
    Args:
        k: float
        e_target: float
        omega_target: float (radians)
    Returns:
        R_eo: ndarray, shape (3,3)
    """

    dm = calculate_dm_for_Reo_matrix(k, omega_target, e_target)
    R_eo = calculate_Reo_matrix_noapprox(dm, omega_target)
    return R_eo

def calculate_RiO_matrix(k, i_target, Omega_target):
    """
    Calculate R_iO matrix.
    Args:
        k: float
        i_target: float (radians)
        Omega_target: float (radians)
    Returns:
        R_iO: ndarray, shape (3,3)
    """
    j = calculate_j_for_RiO_matrix(k, Omega_target, i_target)
    R_iO = calculate_RiO_matrix_noapprox(j, Omega_target)
    return R_iO

def J_func(lmbd, kappa):
    C0 = 4.747336E-3
    C1 = 1.044802E-2
    C2 = -1.517055E-2
    C3 = 2.020210E-1
    C4 = 2.236760

    numerator = (C0 + C1 / kappa + C2 / kappa**2) * np.log(kappa)
    inner_sin = 2 * np.pi * lmbd + C4 - 1 / lmbd
    denominator = lmbd + C3 * (np.sin(inner_sin) - lmbd) * np.exp(-lmbd**2)
    J = numerator / denominator
    return J    

def T_a(a, kappa, alt=True):
    """Время перелета из угловой дальности"""
    B = 0.2721831
    kappa = np.clip(kappa, 1e-6, np.inf)
    if alt:
        T = a*(0.03772064567906565*kappa + 1.405055577366462)*np.log(kappa + 1)+(0.08297934358955021*kappa + 0.009838514316752341)*np.log(kappa)**2
    else:
        T =  (kappa - kappa * B * np.log(kappa)) * a + (kappa * B**2 * np.log(kappa))
    if a < 0.75:
        K = kappa
        L = a
        T = (-L**(-K)*(0.7521363*K + 0.24717593)*(K*(0.0014925372**K*math.log(K + L) - 0.0003217671) - L**(K + 1)*(L + 0.0911687))/(L + 0.0911687)) #3.5e-03
    return T
    
def get_initial_adjoint(a, k, d=1):
    if a < 0.75:
        # --- MARS ---        
        def pr_x_M(L, d):
            y = (-(-0.5683159) + (0.75718486*math.exp(math.cos(L*(L + 1.8499389) + L + L + 0.75718486))**0.008454218 - math.sin(0.8540929 + 0.43165326/L))*(L*math.exp(L) + 0.06105759)/L) #1.7e-04
            return y
        def pr_y_M(L, d):
            y = ((-0.0193943978884244 + 1.3159028*math.cos(0.20418811467131*(L - 0.17080334)*math.log(L)/L)/(math.exp(5.2420635*L) - 0.38545114))*math.sin(0.4104828/L)) #1.1e-04
            return y
        def pv_x_M(L, d):
            y = (0.34306207*(1.5114436**L - (-0.0008686929)*math.exp(math.cos(-1.089295 - 1.5140266/L)))*(-L**(-1.3051801)*L*math.sin(L**(-0.7102793)) + (1.2651104*L)**(-0.7364218))) #7.0e-05
            return y
        def pv_y_M(L, d):
            y = ((math.sin(0.3880472/math.atan(L)) - 0.5640575)/((0.1749562 - math.atan(L))*(math.atan(math.sin(0.36976972/L)) - 1.3752396) + math.atan(L) + 1.2624102) + 0.05609478) #1.2e-04
            return y
        # --- VENUS ---            
        def pr_x_V(L, d):
            y = (-(-0.0015014085)*math.sin(-0.37150827 - 1.6895345/L) - 0.0036338682 + math.atan(math.sin((-0.03401584 - 0.1006823/L)/((L/0.19236025))))/(L - (-0.0099956095)*math.atan(L))) #1.5e-04
            return y
        def pr_y_V(L, d):
            y = ((-(-0.12630376*L*L/(L/math.cos(L) + 0.19825757) + (0.001852162 - 0.00014447162/L)/(L*L)) - 0.06392621)/(L*L)) #3.8e-04
            return y
        def pv_x_V(L, d):
            y = ((math.sin(math.atan(L)) + 0.43953407*math.sin(-0.22335356/L)/L)/2.0870857 - math.atan(math.sin(L - 0.028144019)) - (-0.4978432) - 0.09923751/L) #1.2e-04
            return y
        def pv_y_V(L, d):
            y = ((0.012981842 - 0.033012997/L)/(L + (-0.27790195)*(math.atan(3.7446797*L*L) + (-0.005431808)*math.atan(math.exp(math.cos(-1.356612/L)))))) #3.8e-04
            return y
    else:
        # --- MARS ---
        def pr_x_M(a, d):
            denom = 7.780825627926492 * a - 0.34159993346898454
            sin_arg = 2 * np.pi * a + 0.1231174475945867 + d * 0.5853586584957071 / (a**2 - 1.5690074915306857 * a + 1.9819223815154108)
            exp_arg = -3.424188046763629 * a
            exp_term = d * (-41.26470185582318 + 86.35986725318767 * a - 51.08371071757919 * a**2) * np.exp(exp_arg)
            numerator = 0.20074211987250948
            result = numerator / (denom + np.sin(sin_arg) + exp_term)
            return result
    
        def pr_y_M(a, d):
            cos_arg = 2 * np.pi * a + d * (
                -2.7056930690628103 * a**2 + 5.176300671261158 * a - 2.336378597152512
            ) * np.exp(3.2003639491958467 * a - 3.2205106566099353 * a**2)
            numerator = 0.0015463527047873246 - 0.0031678016585249486 * np.cos(cos_arg)
            denom = a**2 - 0.18328217249773662 * a + 0.11514749689845788
            result = numerator / denom
            return result
    
        def pv_x_M(a, d):
            cos_arg = 2 * np.pi * a + d * (
                -7.277086750486235 * a**2 + 13.74021831427378 * a - 6.262552219285274
            ) * np.exp(1.381195073394106 * a - 2.278956114228774 * a**2)
            numerator = 0.0018661818762522732 - 0.0031537940448213170 * np.cos(cos_arg)
            denom = a**2 - 0.19152227381595716 * a + 0.0993237695309777
            result = numerator / denom
            return result
    
        def pv_y_M(a, d):
            denom = 4.050922375438426 * a - 0.15902042687671913
            sin_arg = 2 * np.pi * a + 0.11429217276196703 + d * 0.012218372217935064 / (a**2 - 2.8347986183365705 * a + 2.06664561825753)
            exp_arg = -5.877538308252977 * a
            exp_term = d * (-540.5981059117084 * a**2 + 958.0032106019531 * a - 415.15730979365355) * np.exp(exp_arg)
            numerator = 0.10456877009148134
            result = numerator / (denom + np.sin(sin_arg) + exp_term)
            return result
    
        # --- VENUS ---
        def pr_x_V(a, d):
            denom = 7.737402704800786 * a - 0.32876870077839637
            sin_arg = 2 * np.pi * a + 0.10377485561964216 + d * 0.5010768929874032 / (a**2 - 1.9514741381243845 * a + 2.4016982504424953)
            exp_arg = -3.086139681061194 * a
            exp_term = d * (-39.740029616989275 + 73.28781124258543 * a - 40.57760476908843 * a**2) * np.exp(exp_arg)
            numerator = -0.2489269721475946
            result = numerator / (denom + np.sin(sin_arg) + exp_term)
            return result
    
        def pr_y_V(a, d):
            cos_arg = 2 * np.pi * a + d * (
                -5.520942046733101*a**2 + 9.93390376988929*a - 4.541315615665989
            ) * np.exp(1.3808955605425999*a - 2.0000002462936357*a**2)
            numerator = -0.006779491667620585 + 0.00432410667098884 * np.cos(cos_arg)
            denom = a**2 + 0.08726450366262754*a - 0.20030536675890054
            result = numerator / denom
            return result
    
        def pv_x_V(a, d):
            cos_arg = 2*np.pi*a + d*(
                -1.786880982902473*a**2 + 3.1517137043764167*a - 1.3891212954291232
            )*np.exp(2.9860241498160076*a-2.699241528126778*a**2)
            numerator = -0.006319471111610397 + 0.004278503661785389*np.cos(cos_arg)
            denom = a**2+0.13118547856852233*a-0.24254361523409607
            result = numerator / denom
            return result
    
        def pv_y_V(a, d):
            denom = 4.0002764433454105*a-0.15629991248717665
            sin_arg = 2*np.pi*a+0.08483203399561368+d*0.008896394730198013/(a**2-2.9131929806240318*a+2.1648040548553382)
            exp_arg = -6.814266658923464*a
            exp_term = d*(-1354.631280683438*a**2+2264.6420824634483*a-951.3449842396692)*np.exp(exp_arg)
            numerator = -0.12867786064634879
            result = numerator / (denom + np.sin(sin_arg) + exp_term)
            return result
    k = np.clip(k, 1e-6,np.inf)
    k1=0.72
    k2=1.52

    # prx
    p1 = pr_x_V(a,d)
    p2 = pr_x_M(a,d)
    g = (p2*k2**(1/4)/np.log(k2) - p1*k1*k2**(-3/4)/np.log(k1))/(1-(k1/k2)**(3/4))
    f = p1*k1/np.log(k1)-g*k1**(3/4)
    pr_x = np.log(k)*(f/k+g*k**(-1/4))

    # pry
    p1 = pr_y_V(a,d)
    p2 = pr_y_M(a,d)
    g = (p2*k2**(3/2)/np.log(k2) - p1*k1*np.sqrt(k2)/np.log(k1))/(1-np.sqrt(k2/k1))
    f = p1*k1/np.log(k1)-g/np.sqrt(k1)
    pr_y = np.log(k)*(f/k+g/(k**(3/2)))

    # pvx
    p1 = pv_x_V(a,d)
    p2 = pv_x_M(a,d)
    g = (p2*k2**(3/2)/np.log(k2) - p1*k1*np.sqrt(k2)/np.log(k1))/(1-np.sqrt(k2/k1))
    f = p1*k1/np.log(k1)-g/np.sqrt(k1)
    pv_x = np.log(k)*(f/k+g/(k**(3/2)))

    # pvy
    p1 = pv_y_V(a,d)
    p2 = pv_y_M(a,d)
    g = (p2*k2**(1/4)/np.log(k2) - p1*k1*k2**(-3/4)/np.log(k1))/(1-(k1/k2)**(3/4))
    f = p1*k1/np.log(k1)-g*k1**(3/4)
    pv_y = np.log(k)*(f/k+g*k**(-1/4))

    pr_0 = np.array([pr_x, pr_y, 0])
    pv_0 = np.array([pv_x, pv_y, 0])
    return pr_0, pv_0

def a_OM(OM, kappa, k):
    """Угловая дальность из оптимальной фазы"""
    A = 0.5433279
    return (OM + k + A * np.exp(-kappa) * np.log(kappa)**2) / (A * (1 + np.exp(-kappa)) * np.log(kappa))

def OM_a(a, kappa):
    """Оптимальная фаза из угловой дальност"""
    A = 0.5433279
    return A * (a * (np.exp(kappa) + 1) - np.log(kappa)) * np.exp(-kappa) * np.log(kappa)
'''
def internalIntegration3D_withJ_TH(t, y):
    mug = 1.0

    res = np.zeros(14)
    r = y[0:3]
    v = y[3:6]
    pr = y[6:9]
    pv = y[9:12]

    nr = np.linalg.norm(r)
    res[0:3] = v
    res[3:6] = -mug * r / nr**3 + pv
    res[6:9] = mug * pv / nr**3 - mug * (3 * np.outer(r, r) @ pv) / nr**5
    res[9:12] = -pr

    res[12] = (np.linalg.norm(pv)**2) / 2  # dJdt
    res[13] = (r[0]*v[1] - r[1]*v[0]) / (nr**2)  # dTHdt

    return res
'''
MUG = 1.0

def internalIntegration3D_withJ_TH(t, y):
    # Распаковка в скаляры (обычно быстрее, чем много мелких numpy-операций)
    rx, ry, rz, vx, vy, vz, prx, pry, prz, pvx, pvy, pvz, _, _ = y

    # r-нормы
    r2 = rx*rx + ry*ry + rz*rz
    inv_r = 1.0 / np.sqrt(r2)
    inv_r2 = 1.0 / r2
    inv_r3 = inv_r * inv_r2          # 1/|r|^3
    inv_r5 = inv_r3 * inv_r2         # 1/|r|^5

    mug_inv_r3 = MUG * inv_r3
    mug_3_inv_r5 = 3.0 * MUG * inv_r5

    # (r · pv) — нужно для r*(r·pv)
    r_dot_pv = rx*pvx + ry*pvy + rz*pvz

    res = np.empty(14, dtype=y.dtype)

    # dr/dt = v
    res[0] = vx
    res[1] = vy
    res[2] = vz

    # dv/dt = -mug * r / |r|^3 + pv
    res[3] = -mug_inv_r3 * rx + pvx
    res[4] = -mug_inv_r3 * ry + pvy
    res[5] = -mug_inv_r3 * rz + pvz

    # dpr/dt = mug * pv / |r|^3 - mug*(3*r*(r·pv))/|r|^5
    # (замена: (np.outer(r, r) @ pv) == r*(r·pv))
    res[6] = mug_inv_r3 * pvx - mug_3_inv_r5 * rx * r_dot_pv
    res[7] = mug_inv_r3 * pvy - mug_3_inv_r5 * ry * r_dot_pv
    res[8] = mug_inv_r3 * pvz - mug_3_inv_r5 * rz * r_dot_pv

    # dpv/dt = -pr
    res[9]  = -prx
    res[10] = -pry
    res[11] = -prz

    # dJ/dt = 0.5 * ||pv||^2
    res[12] = 0.5 * (pvx*pvx + pvy*pvy + pvz*pvz)

    # dTH/dt = (rx*vy - ry*vx) / |r|^2
    res[13] = (rx*vy - ry*vx) * inv_r2

    return res

def orbital_period(r, v, mu=1):
    r = np.asarray(r)
    v = np.asarray(v)
    
    r_norm = np.linalg.norm(r)
    v_norm = np.linalg.norm(v)
    
    E = 0.5 * v_norm**2 - mu / r_norm
    if E >= 0:
        # Неэллиптическая орбита — периода нет
        return None
    
    a = -0.5 * mu / E
    T = 2 * np.pi * a**1.5 / mu**0.5  # Для mu=1 можно опустить деление
    
    return T

def initial_and_final_orbits(sol):
    y0_initial = np.zeros(14)
    y0_initial[0:6] = sol.y[0:6,0]
    t_span = (0, 2*np.pi)
    sol_initial = solve_ivp(internalIntegration3D_withJ_TH,
                    t_span,
                    y0_initial,
                    t_eval=np.linspace(*t_span, 100),
                    method='LSODA',
                    rtol=1e-12,
                    atol=1e-12
                   )
    orbit_initial = sol_initial.y[0:3].T
    
    y0_final = np.zeros(14)
    y0_final[0:6] = sol.y[0:6,-1]
    T_final = orbital_period(sol.y[0:3,-1].T,sol.y[3:6,-1].T, mu=1)
    t_span = (0, T_final)
    sol_final = solve_ivp(internalIntegration3D_withJ_TH,
                    t_span,
                    y0_final,
                    t_eval=np.linspace(*t_span, 100),
                    method='LSODA',
                    rtol=1e-12,
                    atol=1e-12
                   )
    orbit_final = sol_final.y[0:3].T
    return orbit_initial, orbit_final

def rv2orb(r, v, mu=1):  
    """
    r, v: numpy arrays shape (3, N)
    mu: гравитационный параметр

    Возвращает: a, eMag, i, O, o, nu, truLon, argLat, lonPer, p (все размера (N,))
    """
    # Векторное произведение
    h = np.cross(r.T, v.T).T  # shape (3,N)
    k = np.array([[0],[0],[1]])
    k_tile = np.tile(k, (1, r.shape[1]))
    n = np.cross(k_tile.T, h.T).T  # shape (3,N)
    nMag = np.linalg.norm(n, axis=0)
    vMag = np.linalg.norm(v, axis=0)
    rMag = np.linalg.norm(r, axis=0)
    hMag = np.linalg.norm(h, axis=0)
    
    # Эксцентриситет
    e = (1/mu) * ((vMag**2 - mu/rMag) * r - (np.sum(r*v, axis=0)) * v)
    eMag = np.linalg.norm(e, axis=0)
    
    zeta = vMag**2/2 - mu/rMag

    a = np.full_like(eMag, np.nan)
    p = np.full_like(eMag, np.nan)

    idx = eMag != 1
    if np.any(idx):
        a[idx] = -mu / (2*zeta[idx])
        p[idx] = a[idx] * (1 - eMag[idx]**2)
    else:
        a[idx] = np.inf
        p[idx] = (hMag[idx]**2)/mu
    
    # Углы
    def safe_arccos(x):
        return np.arccos(np.clip(x, -1, 1))

    
    i = np.zeros(r.shape[1])
    mask_i = hMag != 0
    i[mask_i] = safe_arccos(h[2, mask_i]/hMag[mask_i])
    
    O = np.zeros(r.shape[1])
    mask_O = nMag != 0
    O[mask_O] = safe_arccos(n[0, mask_O]/nMag[mask_O])
    
    o = np.zeros(r.shape[1])
    mask_o = (nMag != 0) & (eMag != 0)
    o[mask_o] = safe_arccos(np.sum(n[:, mask_o]*e[:, mask_o], axis=0)/(nMag[mask_o]*eMag[mask_o]))
    
    nu = np.zeros(r.shape[1])
    mask_nu = (eMag != 0) & (rMag != 0)
    nu[mask_nu] = safe_arccos(np.sum(e[:, mask_nu]*r[:, mask_nu], axis=0)/(eMag[mask_nu]*rMag[mask_nu]))
    
    lonPer = np.zeros(r.shape[1])
    mask_lonPer = eMag != 0
    lonPer[mask_lonPer] = safe_arccos(e[0, mask_lonPer]/eMag[mask_lonPer])
    
    argLat = np.zeros(r.shape[1])
    mask_argLat = (nMag != 0) & (rMag != 0)
    argLat[mask_argLat] = safe_arccos(np.sum(n[:, mask_argLat]*r[:, mask_argLat], axis=0)/(nMag[mask_argLat]*rMag[mask_argLat]))

    truLon = np.zeros(r.shape[1])
    mask_truLon = rMag != 0
    truLon[mask_truLon] = safe_arccos(r[0, mask_truLon]/rMag[mask_truLon])
    
    # Особые случаи (круговые орбиты и т.п.)
    O[n[0,:] == 0] = 0
    o[np.sum(n*e, axis=0) == 0] = 0
    lonPer[e[0,:] == 0] = 0
    nu[np.sum(e*r, axis=0) == 0] = 0
    argLat[np.sum(n*r, axis=0) == 0] = 0

    # Квадрантные проверки
    idxO = n[1,:] < 0
    O[idxO] = 2*np.pi - O[idxO]

    idxo = e[2,:] < 0
    o[idxo] = 2*np.pi - o[idxo]

    idxnu = np.sum(r*v, axis=0) < 0
    nu[idxnu] = 2*np.pi - nu[idxnu]

    idxlonPer = e[1,:] < 0
    lonPer[idxlonPer] = 2*np.pi - lonPer[idxlonPer]

    idxargLat = r[2,:] < 0
    argLat[idxargLat] = 2*np.pi - argLat[idxargLat]

    idxtruLon = r[1,:] < 0
    truLon[idxtruLon] = 2*np.pi - truLon[idxtruLon]

    return a, eMag, i, O, o, nu, truLon, argLat, lonPer, p

def integrate_traj(r0, v0, p0, t0, T, N=100):
    y0 = np.zeros(14)
    y0[0:3] = r0    # r
    y0[3:6] = v0     # v
    y0[6:12] = p0          # pr
    
    t_span = (t0, T)
    sol = solve_ivp(internalIntegration3D_withJ_TH,
                    t_span,
                    y0,
                    t_eval=np.linspace(*t_span, N),
                    method='LSODA',
                    rtol=1e-12,
                    atol=1e-12
                   )
    traj = sol.y[0:3].T
    rf = sol.y[0:3,-1].T
    vf = sol.y[3:6,-1].T
    Jf = sol.y[12,-1].T
    return rf, vf, Jf, traj

def apply_R(R, pr_0, pv_0):
    pr_0_new = np.linalg.inv(R) @ pr_0
    pv_0_new = np.linalg.inv(R) @ pv_0
    pr_0_new = pr_0_new.T
    pv_0_new = pv_0_new.T
    return pr_0_new, pv_0_new

def get_approx_trajectory(r0, v0, lmbd, kappa, T, t0=0, d=1, i_target=0, O_target=0, e_target=0, o_target=0, calculate_ini_fin=True):
    j = calculate_j_for_RiO_matrix(kappa, O_target, i_target)
    dm = calculate_dm_for_Reo_matrix(kappa, o_target, e_target)
    result_dict = get_approx_trajectory_j_dm(r0, v0, lmbd, kappa, T, t0, d, j, O_target, dm, o_target, calculate_ini_fin)
    return result_dict
    
def get_approx_trajectory_j_dm(r0, v0, lmbd, kappa, T, t0=0, d=1, j=0, O_target=0, dm=0, o_target=0, calculate_ini_fin=True):
    if lmbd < 0.75:
        d=0        
    _, _, _, _, _, _, truLon, _, _, _ = rv2orb(r0.reshape((3,1)), v0.reshape((3,1)), mu=1)
    start_an = truLon[0]
    
    R_eo = calculate_Reo_matrix_noapprox(dm, o_target)
    R_iO = calculate_RiO_matrix_noapprox(j, O_target)
    
    R = calculate_R_matrix(r0, v0)
    
    pr_0, pv_0 = get_initial_adjoint(lmbd, kappa, d)
    pr_0_new, pv_0_new = apply_R(R, pr_0, pv_0)
    p0_new = np.hstack([pr_0_new, pv_0_new])
    
    rf, vf, Jf, traj = integrate_traj(r0, v0, p0_new, t0, T)
    
    a_fix, e_fix, _, _, _, _, _, _, o_fix, _ = rv2orb(rf.reshape((3,1)), vf.reshape((3,1)), mu=1)
    R_eo_2 = calculate_Reo_matrix(a_fix[0], e_fix[0], o_fix[0] + np.pi - start_an)
    R_ini = R_eo_2 @ R
    #КОНЕЦ ИНИЦАЛИЗАЦИИ РЕШЕНИЯ
    
    R_total = R_iO @ R_eo @ R_ini
    p0_new = np.hstack([pr_0_new, pv_0_new])
    y0 = np.zeros(14)
    y0[0:3] = r0    # r
    y0[3:6] = v0     # v
    pr_0, pv_0 = get_initial_adjoint(lmbd, kappa, d=d)
    pr_0_new, pv_0_new = apply_R(R_total, pr_0, pv_0)
    y0[6:9] = pr_0_new          # pr
    y0[9:12] = pv_0_new         # pv
    
    t_span = (0, T)
    sol = solve_ivp(internalIntegration3D_withJ_TH,
                    t_span,
                    y0,
                    t_eval=np.linspace(*t_span, 10),
                    method='DOP853',
                    rtol=1e-10,
                    atol=1e-12,
                    dense_output=False
                   )
    traj = sol.y[0:3].T
    rf = sol.y[0:3,-1].T
    vf = sol.y[3:6,-1].T
    Jf = sol.y[12,-1].T
    result_dict = {'traj':traj}
    result_dict['rf'] = rf
    result_dict['vf'] = vf
    result_dict['Jf'] = Jf

    ae = 149597870.700  # км
    mug = 132712.43994e6  # км^3/с^2
    
    #орбитальный период Земли
    T_earth = 2*np.pi*np.sqrt(np.power(ae,3)/mug)
    
    #коэффициэнты обезразмеривания
    r_unit=ae
    V_unit=np.sqrt(mug/ae)
    T_unit = T_earth/(2*np.pi)
    
    if calculate_ini_fin:
        orbit_initial, orbit_final = initial_and_final_orbits(sol)
        result_dict['orbit_initial'] = orbit_initial
        result_dict['orbit_final'] = orbit_final
    else:
        result_dict['orbit_initial'] = None
        result_dict['orbit_final'] = None
        
    result_dict['T_days'] = T*T_unit/(3600*24)
    return result_dict

def juliandate(year, month, day):
    """
    Переводит календарную дату в юлианскую.
    """
    # Используем формулу из астрономии
    a = int((14 - month) / 12)
    y = year + 4800 - a
    m = month + 12 * a - 3
    JDN = day + int((153 * m + 2) / 5) + 365 * y + int(y / 4) - int(y / 100) + int(y / 400) - 32045
    return float(JDN)

def EAnomaly(e, M):
    """
    Заглушка для решения уравнения Кеплера.
    Возвращает эксцентрическую аномалию E по эксцентриситету e и средней аномалии M.
    Здесь реализован метод Ньютона-Рафсона.
    """
    E = M
    for _ in range(100):
        E_new = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        if abs(E_new - E) < 1e-10:
            break
        E = E_new
    return E

def planet_model_simple(t, planet, dimensionless=False):
    # t в днях (может быть скаляр или массив)
    ae = 149597870.700  # км
    mug = 132712.43994e6  # км^3/с^2

    #орбитальный период Земли
    T_earth = 2*np.pi*np.sqrt(np.power(ae,3)/mug)
    
    #коэффициэнты обезразмеривания
    r_unit=ae
    V_unit=np.sqrt(mug/ae)
    T_unit = T_earth/(2*np.pi)

    if planet == 'Earth':
        a = 1.00 * ae
        e = 1.682781268763978E-02
        Omega = np.pi * 2.198210990481491E+02 / 180
        omega = np.pi * 2.419337242483841E+02 / 180
        i = np.pi * (2.312212390408654E-03) / 180
        M0 = 4.600206682616619E-02
        t0 = juliandate(2016, 1, 3)
    elif planet == 'Mars':
        a = 1.523783440561007 * ae
        e = 9.336536157600901E-02
        Omega = np.pi * 4.950841351899370E+01 / 180
        omega = np.pi * 2.866264313647392E+02 / 180
        i = np.pi * (1.848382482872302E+00) / 180
        M0 = 0
        t0 = 2457690.998223170638
    elif planet == 'Venus':
        a = 0.723327331758308 * ae
        e = 6.751702316628624E-03
        Omega = np.pi * 7.663475158642598E+01 / 180
        omega = np.pi * 5.508545549669039E+01 / 180
        i = np.pi * (3.394389948608993E+00) / 180
        M0 = 0
        t0 = 2457355.851127521135
    elif planet == 'Asteroid2015RE36':
        a = 1.309904433959459 * ae
        e = 0.3903331967297961
        Omega = np.pi * 182.222933497807 / 180
        omega = np.pi * 50.71383675614203 / 180
        i = np.pi * 0.08154670244768725 / 180
        M0 = 0
        t0 = 2460446.638519069714
    elif planet == 'Polyhymnia':
        a = 2.873381502364615 * ae
        e = 0.331735924639039
        Omega = np.pi * 8.42872062375473 / 180
        omega = np.pi * 338.6500899677241 / 180
        i = np.pi * (1.851970677506626) / 180
        M0 = 0
        t0 = 2460470.619383189565
    else:
        raise ValueError("Unknown planet")

    p = a * (1 - e ** 2)
    T = 2 * np.pi * np.sqrt(a ** 3 / mug)   # секунды
    n = 2 * np.pi / (T / 3600 / 24)         # рад/день

    t_arr = np.atleast_1d(t)
    L_t = len(t_arr)

    if L_t == 1:
        M = M0 + (t_arr[0] - t0) * n
        E = EAnomaly(e, M)
        nu = 2 * np.arctan(np.sqrt((1 + e) / (1 - e)) * np.tan(E / 2))
        r, V = orb2rv(p, e, i, Omega, omega, nu, mug)
    elif L_t == 2:
        t2 = t_arr[0] + t_arr[1]
        M = M0 + (t2 - t0) * n
        E = EAnomaly(e, M)
        nu = 2 * np.arctan(np.sqrt((1 + e) / (1 - e)) * np.tan(E / 2))
        r, V = orb2rv(p, e, i, Omega, omega, nu, mug)
    elif L_t > 2:
        M = M0 + (t_arr - t0) * n
        E_vec = np.array([EAnomaly(e, m) for m in M])
        nu_vec = 2 * np.arctan(np.sqrt((1 + e) / (1 - e)) * np.tan(E_vec / 2))
        r, V = orb2rv(np.full(L_t, p), np.full(L_t, e), np.full(L_t, i), 
                      np.full(L_t, Omega), np.full(L_t, omega), nu_vec, mug)
    else:
        raise ValueError("t must be scalar or array")
        
    if dimensionless:
        r = r / r_unit
        V = V / V_unit
        
    return r, V

def orb2rv(p, e, i, O, o, nu, mu):
    """
    Переводит орбитальные элементы в r, v (ECI).
    p, e, i, O, o, nu могут быть скалярами или массивами одинаковой длины.
    mu - гравитационный параметр (скаляр).
    Возвращает r и v: shape (N, 3), где N - число орбит.
    """
    # Приводим входные параметры к массивам-столбцам
    p = np.atleast_1d(p).reshape(-1)
    e = np.atleast_1d(e).reshape(-1)
    i = np.atleast_1d(i).reshape(-1)
    O = np.atleast_1d(O).reshape(-1)
    o = np.atleast_1d(o).reshape(-1)
    nu = np.atleast_1d(nu).reshape(-1)
    
    N = len(p)
    
    # rPQW и vPQW
    cos_nu = np.cos(nu)
    sin_nu = np.sin(nu)
    denom = 1 + e * cos_nu
    rPQW = np.stack([
        p * cos_nu / denom,
        p * sin_nu / denom,
        np.zeros(N)
    ], axis=1)
    
    sqrt_mu_p = np.sqrt(mu / p)
    vPQW = np.stack([
        -sqrt_mu_p * sin_nu,
        sqrt_mu_p * (e + cos_nu),
        np.zeros(N)
    ], axis=1)
    
    # Предварительные косинусы/синусы
    cO = np.cos(O)
    sO = np.sin(O)
    co = np.cos(o)
    so = np.sin(o)
    ci = np.cos(i)
    si = np.sin(i)

    # Матрица поворота PQW2IJK для каждого объекта
    PQW2IJK = np.empty((N, 3, 3))
    PQW2IJK[:,0,0] = cO*co - sO*so*ci
    PQW2IJK[:,0,1] = -cO*so - sO*co*ci
    PQW2IJK[:,0,2] = sO*si
    PQW2IJK[:,1,0] = sO*co + cO*so*ci
    PQW2IJK[:,1,1] = -sO*so + cO*co*ci
    PQW2IJK[:,1,2] = -cO*si
    PQW2IJK[:,2,0] = so*si
    PQW2IJK[:,2,1] = co*si
    PQW2IJK[:,2,2] = ci

    # Умножаем матрицу на rPQW и vPQW для каждого объекта (batch matrix-vector product)
    rECI = np.einsum('nij,nj->ni', PQW2IJK, rPQW)
    vECI = np.einsum('nij,nj->ni', PQW2IJK, vPQW)

    return rECI, vECI

def make_F_function(r0, v0, lmbd, kappa, t0,  d, i_target, O_target, e_target, o_target, calculate_ini_fin=False, calculate_full_traj=False, L_correction=False):
    [a,eMag,i,O,o,nu,truLon,argLat,lonPer,p] = rv2orb(r0.T,v0.T,1)
    start_an = truLon[0]
    j = calculate_j_for_RiO_matrix(kappa, O_target-start_an, i_target)
    dm = calculate_dm_for_Reo_matrix(kappa, o_target-start_an, e_target)
    if L_correction:
        lmbd_old = lmbd
        lmbd = correct_lambda_simple(lmbd, kappa, dm, o_target-start_an)
        print('L_correction', lmbd_old, '->', lmbd)
    x_initial = np.array([dm, j, O_target, o_target, kappa, lmbd])
    def F(x):
        dm = x[0]
        j  = x[1]
        O_target = x[2]
        o_target = x[3]
        kappa = x[4]
        lmbd = x[5]
        if lmbd<=0:
            raise ValueError('ILTT angular distance must be positive')
        
        T = 2*np.pi*T_a(lmbd, kappa)
        #print("F:", lmbd, kappa, T)
        result_dict = get_approx_trajectory_j_dm_v2(r0, v0, lmbd, kappa, T, t0, d, j, O_target, dm, o_target, calculate_ini_fin, calculate_full_traj)
        return result_dict
    
    return F, x_initial

def ang_err(target, val):
    # в (-pi, pi]
    return np.arctan2(np.sin(val - target), np.cos(val - target))
    
def create_loss_fuction(F, t_start, planet_end):
    def loss_function(x):
        result_dict = F(x)
        
        T_days = result_dict['T_days']
        
        end_pos, end_vel = planet_model_simple(t_start+T_days, planet_end,dimensionless=True)
        [a_end,e_end,i_end,Omega_end,omega_end,nu,truLon_end,argLat,lonPer_end,p] = rv2orb(end_pos.T,end_vel.T,1)

        i_target = i_end[0]
        O_target = Omega_end[0]
        e_target = e_end[0]
        o_target = lonPer_end[0]
        a_target = a_end[0]
        truLon_target = truLon_end[0]
        
        rf = result_dict['rf']
        vf = result_dict['vf']
        [a,eMag,i,O,o,nu,truLon,argLat,lonPer,p] = rv2orb(rf.reshape((3,1)), vf.reshape((3,1)),1)

        a_res = a_target - a[0]
        i_res = i_target - i[0]
        e_res = e_target - eMag[0]

        #print("O_target:", O_target, "O:", O[0])
        O_vec_target = np.array([np.cos(O_target),np.sin(O_target)])
        O_vec = np.array([np.cos(O[0]),np.sin(O[0])])
        O_res = 1-np.dot(O_vec_target,O_vec)
        
        #print("o_target:", o_target, "o:", lonPer[0])
        o_vec_target = np.array([np.cos(o_target),np.sin(o_target)])
        o_vec = np.array([np.cos(lonPer[0]),np.sin(lonPer[0])])
        o_res = 1-np.dot(o_vec_target,o_vec)
        
        #print("L_target:", truLon_target, "L:", truLon[0])
        L_vec_target = np.array([np.cos(truLon_target),np.sin(truLon_target)])
        L_vec = np.array([np.cos(truLon[0]),np.sin(truLon[0])])
        L_res = 1-np.dot(L_vec_target,L_vec)
        #L_res = 0

        O_res = ang_err(O_target, O[0])
        o_res = ang_err(o_target, lonPer[0])
        L_res = ang_err(truLon_target, truLon[0])
        
        res = np.array([a_res, i_res, e_res, O_res, o_res, L_res])
        #res_r = end_pos[0]-result_dict['rf']
        #res_v = end_vel[0]-result_dict['vf']
        #res = np.hstack([res_r, res_v])
        return res 
    return loss_function

def k_order(max_abs_k):
    yield 0
    for m in range(1, max_abs_k + 1):
        yield -m
        yield m

def find_min_positive_lmbd(OM, a0, a_OM, max_abs_k=200):
    best_val = np.inf
    best_k = None

    for k in k_order(max_abs_k):
        try:
            val = float(a_OM(OM, a0, k)[0])
        except Exception:
            continue  # пропускаем неудачные вызовы
        if np.isfinite(val) and val > 0 and val < best_val:
            best_val = val
            best_k = k

    if best_k is None:
        return None, None  # положительных не найдено в заданном диапазоне
    return best_val, best_k

def get_approx_trajectory_j_dm_v2(r0, v0, lmbd, kappa, T, t0=0, d=1, j=0, O_target=0, dm=0, o_target=0, calculate_ini_fin=True, calculate_full_traj=False):
    #if lmbd < 0.75:
    #    d=0
        
    #d = np.tanh((lmbd-0.74)*20)/2+0.5
    [a,eMag,i,O,o,nu,truLon,argLat,lonPer,p] = rv2orb(r0.T,v0.T,1)
    start_an = truLon[0]
    
    R_eo = calculate_Reo_matrix_noapprox(dm, o_target-start_an)
    R_iO = calculate_RiO_matrix_noapprox(j, O_target-start_an)
    
    R = calculate_R_matrix(r0, v0)
    
    pr_0, pv_0 = get_initial_adjoint(lmbd, kappa, d)
    pr_0_new, pv_0_new = apply_R(R, pr_0, pv_0)
    p0_new = np.hstack([pr_0_new, pv_0_new])
    
    #КОНЕЦ ИНИЦАЛИЗАЦИИ РЕШЕНИЯ
    
    R_total = R_iO @ R_eo @ R
    #R_total = R
    p0_new = np.hstack([pr_0_new, pv_0_new])
    y0 = np.zeros(14)
    y0[0:3] = r0[0]    # r
    y0[3:6] = v0[0]    # v
    pr_0, pv_0 = get_initial_adjoint(lmbd, kappa, d=d)
    pr_0_new, pv_0_new = apply_R(R_total, pr_0, pv_0)
    y0[6:9] = pr_0_new          # pr
    y0[9:12] = pv_0_new         # pv
    
    t_span = (0, T)
    if calculate_full_traj:
        t_span_size = 1000
    else:
        t_span_size = 5
    
    sol = solve_ivp(internalIntegration3D_withJ_TH,
                    t_span,
                    y0,
                    t_eval=np.linspace(*t_span, t_span_size),
                    method='DOP853',
                    rtol=1e-10,
                    atol=1e-12
                   )
    traj = sol.y[0:3].T
    rf = sol.y[0:3,-1].T
    vf = sol.y[3:6,-1].T
    Jf = sol.y[12,-1].T
    result_dict = {'traj':traj}
    result_dict['rf'] = rf
    result_dict['vf'] = vf
    result_dict['Jf'] = Jf

    ae = 149597870.700  # км
    mug = 132712.43994e6  # км^3/с^2
    
    #орбитальный период Земли
    T_earth = 2*np.pi*np.sqrt(np.power(ae,3)/mug)
    
    #коэффициэнты обезразмеривания
    r_unit=ae
    V_unit=np.sqrt(mug/ae)
    T_unit = T_earth/(2*np.pi)
    a_unit=(np.sqrt(mug)/ae)**2; #км/с^2
    
    if calculate_ini_fin:
        orbit_initial, orbit_final = initial_and_final_orbits(sol)
        result_dict['orbit_initial'] = orbit_initial
        result_dict['orbit_final'] = orbit_final
    else:
        result_dict['orbit_initial'] = None
        result_dict['orbit_final'] = None
        
    if calculate_full_traj:
        result_dict['pv'] = 1e6*a_unit*sol.y[9:12].T #мм/c2
    else:
        result_dict['pv'] = None
        
    result_dict['T_days'] = T*T_unit/(3600*24)
    result_dict['T_span_days'] = np.linspace(*t_span, t_span_size)*T_unit/(3600*24)
    return result_dict

def m_p(J, m0, eta, N_max, J_dimensionless=True):
    """
    Вычисляет значение расход топлива по формуле:
    m_p(t) = m0 - m0 / (1 + J(t)*m0/(eta*N_max))
    """
    if J_dimensionless:
        ae = 149597870.700  # км
        mug = 132712.43994e6  # км^3/с^2

        r_unit = ae
        V_unit = np.sqrt(mug/ae)
        
        #орбитальный период Земли
        T_earth = 2*np.pi*np.sqrt(np.power(ae,3)/mug)
        
        T_unit = T_earth/(2*np.pi)
        J_unit = np.power(r_unit,2)/np.power(T_unit,3)
        J = J*J_unit*1e6
        
    denominator = 1 + (J * m0) / (eta * N_max)
    result = m0 - m0 / denominator
    return result

def sorted_local_minima_with_threshold(res_r_list, lmbd_space, threshold=0):
    arr = np.array(res_r_list)
    lmbd_space = np.array(lmbd_space)
    local_min_mask = (arr[1:-1] < arr[:-2]) & (arr[1:-1] < arr[2:])
    local_min_indices = np.where(local_min_mask)[0] + 1
    
    # ОТБРАКОВКА минимумов с res_r_list > 0.5
    valid_min_indices = local_min_indices[arr[local_min_indices] <= 0.5]
    
    sorted_min_indices = valid_min_indices[np.argsort(arr[valid_min_indices])]
    
    selected_indices = []
    selected_lmbds = []
    for idx in sorted_min_indices:
        lmbd_val = lmbd_space[idx]
        if not selected_lmbds or np.all(np.abs(lmbd_val - np.array(selected_lmbds)) >= threshold):
            selected_indices.append(idx)
            selected_lmbds.append(lmbd_val)
    return np.array(selected_indices)
    
if __name__ == "__main__":
    # Начальные условия
    r0 = np.array([1.0, 0.0, 0.0])
    v0 = np.array([0.0, 1.0, 0.0])
    t0 = 0
    #угловая дальность
    lmbd = 4.0
    #соотношение полуосей
    kappa = 1.52
    #вычисляем время перелёта
    T = 2*np.pi*T_a(lmbd, kappa)
    #D-коэффициэнты
    d=1
    
    #наклонение в радианах
    i_target = 10*np.pi/180 
    #восходящий узел в радианах
    O_target = 30*np.pi/180
    #эксцентриситет
    e_target = 0.1 
    #аргумент перицентра в радианах
    o_target = 90*np.pi/180 
    
    result_dict = get_approx_trajectory(r0, v0, lmbd, kappa, T, t0,  d, i_target, O_target, e_target, o_target)
    traj = result_dict['traj']
    orbit_initial = result_dict['orbit_initial']
    orbit_final = result_dict['orbit_final']
    
    # График
    fig = plt.figure(5)
    ax = fig.add_subplot(111, projection='3d')
    plt.gca().set_facecolor('white')
    ax.plot([0],[0],[0],'ko',label='',alpha=0)  # невидимая точка центра
    
    ax.plot([traj[0,0]], [traj[0,1]], [traj[0,2]], 'bo', label='Начальная точка')
    ax.plot([traj[-1,0]], [traj[-1,1]], [traj[-1,2]], 'ro', label='Конечная точка')
    ax.plot(traj[:,0], traj[:,1], traj[:,2], color='cyan', linewidth=1)
    ax.plot(orbit_initial[:,0], orbit_initial[:,1], orbit_initial[:,2], 'k--', linewidth=1.5,label='Начальная орбита')
    ax.plot(orbit_final[:,0], orbit_final[:,1], orbit_final[:,2], 'k-.', linewidth=1.5,label='Конечная орбита')
    
    ax.set_xlabel('x, DU')
    ax.set_ylabel('y, DU')
    ax.set_zlabel('z, DU')
    ax.view_init(elev=90., azim=-90)
    ax.legend()
    plt.grid(True)
    plt.axis('equal')
    plt.show()

    rf = result_dict['rf']
    vf = result_dict['vf']
    [a,eMag,i,O,_,_,_,_,lonPer,_] = rv2orb(rf.reshape((3,1)), vf.reshape((3,1)),1)
    print("Тестовый запуск успешен")
    print("Конечная орбита:")
    print("   Большая полуось:", a[0])
    print("   Эксцентриситет:", eMag[0])
    print("   Наклонение:", i[0])
    print("   Долгота восходящего узла:", O[0])
    print("   Аргумент перицентра:", lonPer[0])

def correct_lambda_simple(L0, K0, dm_total, omega):
    """
    Одна итерация коррекции λ (lmbd) по линейной модели:
        ΔL ≈ S_lam_approx_v2(ω, L, K) * dm_total.

    Вход:
      L0, K0   — исходные lmbd, kappa
      dm_total — заданный dm
      omega    — аргумент перицентра (рад)

    Выход:
      L_corr — скорректированная lmbd
    """
    L = float(L0)
    K = float(K0)

    # S_L: рад/ед.dm
    S_L = float(S_lam_approx_v2(omega, L, K))

    dL = S_L * dm_total/(2*np.pi) 

    # корректируем λ в витках
    L_corr = L - dL

    return L_corr

def S_lam_approx_v2(omega, L, K):
    L = np.atleast_1d(np.float64(L))
    K = np.atleast_1d(np.float64(K))
    def c0_lam_approx(L, K):
        p = L*2*np.pi
        y = ((L*np.arctan(K*L**2) + 0.82187337)*(0.0058871657*np.cos(56.677177*L) - 0.40101022 - 0.0153615268740028/K)*np.log(K)) #2.6e-02
        return y
    
    def a1_lam_approx(L, K):
        p = L*2*np.pi
        #y = ((-K*(9.778846 - 2.2222493*K)*np.sin(6.32132*L + 1.2806617) - 6.658384 + 5.520658*L**(-L)*(1.2462397 - K))*np.log(K**L)) #1.2e00
        y = ((p + (-1.78555919714402*np.cos(p)*np.arctan(K) - 2.4934194)*(K*(-np.sqrt(p) + np.sin(p) + 4.571423) + p - 3.6274443))*np.log(K)) #1.1e00
        return y
    
    def b1_lam_approx(L, K):
        p = L*2*np.pi
        #y = ((np.arctan(K) + 0.14873384)*(K/L + (-K - 5.499115*L + np.cos(L))*np.cos(6.361151*L - 2.0215979) - 3.2728057 + 7.0053897/K)*np.log(K)) #7.2e-01
        y = (2.2276373*(0.98109335 - K)*((0.2957547*p + 1.29198500544168)*np.sin(p) - np.cos(p) + 0.85754347 + (np.sin(p + np.sqrt(p*np.arctan(np.arctan(K))) + 1.611204) - 2.5816476)/K)) #6.9e-01
        return y
    
    def a3_lam_approx(L, K):
        p = L*2*np.pi
        y = (p*(-0.112247035*(K + np.sin(1.18486290247571*K))*np.cos(p - 2.7900786/p) - 0.18705241)*np.log(K) - (K**2/p)**1.6229355) #2.2e-01
        return y
    
    def b3_lam_approx(L, K):
        p = L*2*np.pi
        y = ((K - 0.99315286)*(L + 0.8012159)*(np.sin(L/(-0.15757908) - (-0.36855963)) + 0.91364694/((L + 0.967995)**K + np.sin(L/(-0.15322572))))/1.5039495) #1.1e-01
        return y
    return (c0_lam_approx(L, K)
          + a1_lam_approx(L, K) * np.cos(omega)
          + b1_lam_approx(L, K) * np.sin(omega)
          + a3_lam_approx(L, K) * np.cos(3 * omega)
          + b3_lam_approx(L, K) * np.sin(3 * omega))
