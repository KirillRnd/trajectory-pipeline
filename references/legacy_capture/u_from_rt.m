function u = u_from_rt(t,r,param)
%UNTITLED4 Summary of this function goes here
%   Detailed explanation goes here

ae = 149597870700;
r_norm = norm(r)/ae;
N_degradation_percent = 1-t*param.k_degradation/param.T_earth;
if N_degradation_percent < 0
    N_degradation_percent=0;
end
N = N_degradation_percent*param.Nj0/(r_norm^1.7)-param.N_margin;
if N > 450
    N = 450;
end
Isp = -0.0006*N^2 + 1.0584*N + 999.2504; %секунды
g0=9.80665; %м/с2
u = g0 * Isp;% %скорость истечения
if N < 200
    u = 0;
end
end