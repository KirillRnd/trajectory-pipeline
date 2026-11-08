from ApproxTraj import *
from scipy.optimize import root

if __name__ == "__main__":
    #ПРИМЕР С ПЕРЕЛЁТОМ МЕЖДУ ОРБИТОЙ ЗЕМЛИ И ОРБИТОЙ МАРСА
    #дата старта
    t_start=juliandate(2026,9,1)
    t0 = 0
    #мощность, доступная ЭРДУ
    N=1350
    #полная масса КА
    m0=367
    #КПД ЭРДУ
    eta=0.45
    planet_start = 'Earth'
    planet_end = 'Mars'
    d = 1
    lmbd = 0.75
    #
    end_pos, end_vel = planet_model_simple(t_start, planet_end,dimensionless=True)
    [a,eMag,i,O,o,nu,truLon,argLat,lonPer,p] = rv2orb(end_pos.T,end_vel.T,1)
    Omega_end = O
    omega_end = lonPer
    i_end = i
    e_end = eMag
    kappa = a[0]
    T = 2*np.pi*T_a(lmbd, kappa)
    ae = 149597870.700  # км
    mug = 132712.43994e6  # км^3/с^2
    
    #орбитальный период Земли
    T_earth = 2*np.pi*np.sqrt(np.power(ae,3)/mug)
    T_unit = T_earth/(2*np.pi)
    
    [r0, v0] = planet_model_simple(t_start, planet_start,dimensionless=True)
    
    r0 = r0[0]
    v0 = v0[0]
    
    i_target = i_end[0]
    O_target = Omega_end[0]
    e_target =  e_end[0]
    o_target = omega_end[0]
    a_target = kappa
    
    F, x_initial = make_F_function(r0, v0, lmbd, kappa, T, t0, d, i_target, O_target, e_target, o_target)
    loss = create_loss_fuction(F, a_target, i_target, O_target, e_target, o_target)
    res = root(loss, x_initial, method='hybr')  # hybr — без явного использования градиента
    result_dict = F(res.x)
    traj = result_dict['traj']
    mass_consumption = m_p(result_dict['Jf'], m0, eta, N)
    
    kappa = res.x[4]
    T = 2*np.pi*T_a(lmbd, kappa)
    end_pos, end_vel = planet_model_simple(t_start+T_unit*T/(3600*24), planet_end,dimensionless=True)
    
    print('Расход топлива (Smart-1)', np.round(mass_consumption, 1), 'кг')
    print('Продолжительность перелёта', np.round(T_unit*T/(3600*24), 1), 'сут')
    _, _, _, orbit_initial = integrate_traj(r0, v0, 0, 0, orbital_period(r0, v0, mu=1), N=100)
    _, _, _, orbit_final = integrate_traj(end_pos, end_vel, 0, 0, orbital_period(end_pos, end_vel, mu=1), N=100)
    
    # График
    fig = plt.figure(5)
    ax = fig.add_subplot(111, projection='3d')
    plt.gca().set_facecolor('white')
    ax.plot([0],[0],[0],'ko',label='',alpha=0)  # невидимая точка центра
    
    ax.plot([traj[0,0]], [traj[0,1]], [traj[0,2]], 'bo', label='Начальная точка')
    ax.plot(end_pos[0][0], end_pos[0][1], end_pos[0][2], 'go', label='Планета')
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
    print("Пример перелёта на орбиту Марса")
    print("(Без решения задачи встречи)")
    print("Конечная орбита:")
    print("   Большая полуось:", a[0])
    print("   Эксцентриситет:", eMag[0])
    print("   Наклонение:", i[0])
    print("   Долгота восходящего узла:", O[0])
    print("   Аргумент перицентра:", lonPer[0])