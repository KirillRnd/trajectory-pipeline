function [J, c, ceq, border_values] = fun2min_core(X, param)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here
c =[];

delta_t_start = X(9);
start_date = param.t_start+delta_t_start;
st.t = start_date;
st.planet = 'Earth';
st.mode = 'Simple';

[earth_r_0, earth_v_0]=planetModel(st);
earth_r_0=earth_r_0'*1e+03;
earth_v_0=earth_v_0'*1e+03;

% Исходные r, v, m (7 переменных)
r0 = earth_r_0;  % нач. радиус (пример — ~ORB высота)
v0 = earth_v_0;   % нач. скорость
mUsed0 = 0;           % израсходованная масса на t=0 (обычно 0)


y0 = param.Y0;

dv0=X(1:3)*param.V_unit;
pr0=param.pr_scaler*X(4:6)/param.r_unit;
pm0=X(7);
t_end = X(8);
y0(1:3) = r0;
y0(4:6)=dv0+v0;
y0(8:10)=pr0;
y0(14)=pm0;

tspan = [0, t_end*param.T_earth];  % интервал времени


options = odeset('RelTol',1e-10,'AbsTol',1e-10);
options = odeset(options, 'Events',@(s, y) eventIntegrationTrajStopM(s, y, param));
[~, y_sol] = ode15s(@(t, Y) integrate_dmdt_optimal(t, Y, param), tspan, y0, options);
%разбираем все параметры
r_end = y_sol(end,1:3);
v_end = y_sol(end,4:6);
m_end = y_sol(end,7);
pr_end = y_sol(end,8:10);
pv_end = y_sol(end,11:13);
pm_end = y_sol(end,14);

target_date = param.t_start+tspan(end)/(3600*24);
if isfield(param, 'target_time_uses_delta_start') && param.target_time_uses_delta_start
    target_date = start_date+tspan(end)/(3600*24);
end
st.t = target_date;
st.planet = param.target_body;
st.mode = 'Simple';

[target_r_f, target_v_f]=planetModel(st);
target_r_f=target_r_f*1e+03;
target_v_f=target_v_f*1e+03;

% для учёта затрат хар. скорости на границе сферы Хилла
if isfield(param, 'for_r_soi') && param.for_r_soi == 1            % средн. радиус орбиты Венеры, м (0.723 а.е.)
    R_venus  = 6.0518e6;  
    r_hat = target_r_f / norm(target_r_f);            % радиальное направление
    h_vec = cross(target_r_f, target_v_f);            % угловой момент
    n_hat = h_vec / norm(h_vec);
    dR = R_venus*(r_hat*param.P(1)+n_hat*param.P(2));
    target_r_f = dR + target_r_f;
end
if strcmp('встреча',param.type_of_problem)
    r_res = (r_end-target_r_f)/param.r_unit;
    v_res = (v_end-target_v_f)/param.V_unit;
    %pm_res = pm_end;
    res = [r_res,v_res];
elseif strcmp('пролёт',param.type_of_problem)
    r_res = (r_end-target_r_f)/param.r_unit;
    pv_res = pv_end;
    res = [r_res];
elseif strcmp('захват',param.type_of_problem)
    r_res = (r_end-target_r_f)/param.r_unit;
    v_res = (v_end-target_v_f)/param.V_unit;
    dv_res = param.dv_target/param.V_unit - norm(v_res);
    pv_res = pv_end;
    dv_direction = cross(v_res, pv_res);
    res = [r_res,dv_res,dv_direction];
end

J = m_end;

%J=1;
ceq = res;
border_values = struct();
end
