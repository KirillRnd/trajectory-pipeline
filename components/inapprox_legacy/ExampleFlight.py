from ApproxTraj import *
from scipy.optimize import root

if __name__ == "__main__":
    #ПРИМЕР С МЕЖПЛАНЕТНЫМ ПЕРЕЛЁТОМ ЗЕМЛЯ-МАРС
    #дата старта
    t_start=juliandate(2026,9,1)
    t0=0
    d=1
    #мощность, доступная ЭРДУ
    N=1350
    #полная масса КА
    m0=367
    #КПД ЭРДУ
    eta=0.45
    planet_start = 'Earth'
    planet_end = 'Mars'
    
    lmbd_space = np.linspace(0.75,3,100)
    #расход топлива
    mass_list = []
    #продолжительность перелёта
    T_list = []
    res_r_list = []
    x0 = None
    for counter, lmbd in enumerate(list(lmbd_space)):
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
        if x0 is None:
            res = root(loss, x_initial, method='hybr')  # hybr — без явного использования градиента
        else:
            res = root(loss, x0, method='hybr')  # hybr — без явного использования градиента
        x0 = res.x
        result_dict = F(res.x)
        traj = result_dict['traj']
        mass_consumption = m_p(result_dict['Jf'], m0, eta, N)
    
        
        kappa = res.x[4]
        T = 2*np.pi*T_a(lmbd, kappa)
        end_pos, end_vel = planet_model_simple(t_start+T_unit*T/(3600*24), planet_end,dimensionless=True)
        T_list.append(T_unit*T/(3600*24))
        
        mass_list.append(mass_consumption)
        res_r = np.linalg.norm(end_pos[0]-result_dict['rf'])
        res_r_list.append(res_r)
        print(counter, '/', len(lmbd_space), end='\r')
        
    indices = sorted_local_minima_with_threshold(res_r_list, lmbd_space, threshold=0.5)
    m_ok = np.array(mass_list)[indices]
    T_ok = np.array(T_list)[indices]
    # Получаем индексы сортировки по T_ok
    sorted_indices = np.argsort(T_ok)
    
    # Сортируем оба массива по этим индексам
    m_sorted = m_ok[sorted_indices]
    T_sorted = T_ok[sorted_indices]
    print("Межпланетный перелёт Земля-Марс")
    print("Расход топлива на примере Smart-1")
    print("Дата старта: 2026.09.01")
    print("Список решений:")
    # Выводим попарно
    for m, T in zip(m_sorted, T_sorted):
        
        print("Продолжительность перелёта:", np.round(T,1), "сут.")
        print("Расход топлива:", np.round(m,1), "кг.")
        print("----------------------------")
