function thrust_N = evaluate_ummp_thrust_force(t_s, y, param)
%EVALUATE_UMMP_THRUST_FORCE Reconstruct bang-bang thrust command in newtons.

r = y(1:3);
m_used = y(7);
pv = y(11:13);
pm = y(14);

u = u_from_rt(t_s, r, param);
gamma_max = gamma_max_from_rt(t_s, r, param);
mass = param.m0 - m_used;

pv_norm = norm(pv);
if pv_norm < 1e-12
    e_star = [0; 0; 0];
else
    e_star = pv / pv_norm;
end

S = param.m_compensation * (1 + pm) ...
    - (u / mass) * dot(pv, e_star);

eps_tol = 1e-8;
if S < -eps_tol
    gamma_star = gamma_max;
else
    gamma_star = 0;
end

thrust_N = gamma_star * u;
end
