import numpy as np
from numpy.linalg import norm
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import pickle
from matplotlib.colors import hsv_to_rgb
from scipy.optimize import least_squares


def cr3bp_equations(t, state):
    x, y, vx, vy = state
    r1 = ((x + mu) ** 2 + y ** 2) ** 0.5
    r2 = ((x - 1 + mu) ** 2 + y ** 2) ** 0.5

    Ux = x - (1 - mu) * (x + mu) / r1 ** 3 - mu * (x - 1 + mu) / r2 ** 3
    Uy = y - (1 - mu) * y / r1 ** 3 - mu * y/ r2 ** 3

    return np.array([vx,
                     vy,
                     2 * vy + Ux,
                    -2 * vx + Uy])


def F(z, x0):
    vy0, T = z
    y_init = np.array([x0, 0.0,  0.0, vy0])

    sol = solve_ivp(cr3bp_equations, [0, T], y_init,  method="LSODA",
                   rtol=1e-12, atol=1e-12, t_eval=np.linspace(0, T, 500))

    yT = sol.y[:, -1]          # состояние в t = T
    
    return np.hstack((np.sqrt(yT[1]**2 + (yT[0] - x0) ** 2), np.sqrt((yT[3] - vy0)**2 + yT[2]**2)))



def F_1(z, x0):
    vy0, T = z
    y_init = np.array([x0, 0.0,  0.0, vy0])

    sol = solve_ivp(cr3bp_equations, [0, T], y_init,  method="LSODA",
                   rtol=1e-12, atol=1e-12, t_eval=np.linspace(0, T, 500))

    yT = sol.y[:, -1]          # состояние в t = T
    
    return np.hstack(((yT[0] - x0) ** 2, (yT[3] - vy0)**2))


def jacobian(Ffun, z, x0, h=1e-10):
    J = np.zeros((2, 2))
    for i in range(2):
        dz = np.zeros_like(z)
        dz[i] = h
        fp = Ffun(z + dz, x0)
        fm = Ffun(z - dz, x0)
        J[:, i] = (fp - fm) / (2 * h)
    return J

def differential_correction(
    func, 
    x0, 
    vy_est, 
    T_est, 
    max_iter=50, 
    tol=1e-16,
    vy_bounds=(None, None),  
    T_bounds=(None, None)   
):
   
    z = np.array([vy_est, T_est], dtype=float)
    alpha = 1e-6  # Параметр для предобуславливания
    min_singular = 1e-8  
    
    for k in range(max_iter):
        Fz = func(z, x0)
        current_norm = norm(Fz)
        if current_norm < tol:
            print(f'Сошлось за {k} итераций, ||F|| = {current_norm:.2e}')
            return z

        J = jacobian(func, z, x0)
        
        # Предобуславливание
        U, s, Vh = np.linalg.svd(J)
        cond_number = s[0]/s[-1] 
        
      
        if cond_number > 1e10:
            print(f'Предупреждение: плохая обусловленность (κ={cond_number:.1e}), применяю регуляризацию')
            s_inv = np.zeros_like(s)
            s_inv[s > min_singular] = 1 / s[s > min_singular]
            delta = Vh.T @ (s_inv * (U.T @ Fz))
        else:
           
            JTJ = J.T @ J
            JTJ_reg = JTJ + alpha * np.eye(2)
            delta = np.linalg.solve(JTJ_reg, J.T @ Fz)

        step = 1.0
        for _ in range(5):  
            new_z = z - step * delta
            
            
            if vy_bounds[0] is not None:
                new_z[0] = np.clip(new_z[0], vy_bounds[0], vy_bounds[1])
            if T_bounds[0] is not None:
                new_z[1] = np.clip(new_z[1], T_bounds[0], T_bounds[1])
            
            new_Fz = func(new_z, x0)
            if norm(new_Fz) < current_norm:
                break
            step *= 0.5
        
        z = z - step * delta
        
    
        if vy_bounds[0] is not None:
            z[0] = np.clip(z[0], vy_bounds[0], vy_bounds[1])
        if T_bounds[0] is not None:
            z[1] = np.clip(z[1], T_bounds[0], T_bounds[1])
        
        print(f'x0={x0:.3e}, k={k:2d}: ||F||={current_norm:.3e}, |Δz|={norm(delta):.3e}, step={step:.2f}, κ={cond_number:.1e}')
    
    print(f'Достигнуто максимальное число итераций ({max_iter}), ||F||={current_norm:.3e}')
    return z

mu = 1e-3
N = 50
x0 = np.linspace(-mu+0.15, 0.7,  N)
y0 =  0.0     
vx0_est = 0.0
vy0_est = (np.sqrt((1-mu)/(x0 + mu)) - (x0 + mu))
T_est = 2 * np.pi * (x0 + mu) / vy0_est

for i in range(N):

    vy_bounds = (vy0_est[i] - 0.05, vy0_est[i] + 0.05)
    T_bounds = (T_est[i] - 1, T_est[i] +1)  
    vy01, T1 = differential_correction(F,
                                            x0[i],
                                            vy0_est[i],
                                            T_est[i], tol=2e-8,  vy_bounds=vy_bounds,
        T_bounds=T_bounds)
    y_initial = np.array([x0[i], 0, 0, vy01])
    vy0, T = differential_correction(F_1,
                                    x0[i],
                                    vy01,
                                    T1, tol=1e-16, vy_bounds=vy_bounds,
    T_bounds=T_bounds)

    y = np.array([x0[i], 0.0, 0.0, vy0])


    sol_sat_tmp = solve_ivp(cr3bp_equations,t_span = (0, T),y0 = y,method="LSODA",atol=1e-12,rtol=1e-12, t_eval=np.linspace(0, T, 500))
    plt.plot(sol_sat_tmp.y[0,:], sol_sat_tmp.y[1, :])
plt.show()