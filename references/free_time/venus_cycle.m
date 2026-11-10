%параметры космического аппарата и некоторые константы
%clc;
%clear;
standart_parameters
param.type_of_problem = "захват";
param.target_body = "Venus";

param.t_start = juliandate(2032,11,1);%дата старта
r_SOI = 616000;
%param.dv_target = 1000*sqrt(2*324859/r_SOI);
param.dv_target = 379.5;
param.pr_scaler = 1000;

%%очень большой перебор
delta_t_starts = 0:1:365*10+5;
N_count_1 = length(delta_t_starts);
param.t_start_zero = juliandate(2027,1,1);

resrf_massive = zeros(N_count_1,1);%невязка положения
revf_massive = zeros(N_count_1,1);%невязка скорости
Vhar_massive = zeros(N_count_1,1);%характеристическая скорость самого КА
Vinf_massive = zeros(N_count_1,1);%отлётная скорость
mf_massive = zeros(N_count_1,1);%расход топлива
t_end_massive = zeros(N_count_1,1);%время перелёта
active_days_massive = zeros(N_count_1,1);%время работы дигателя
checked = zeros(N_count_1,1);%проверка вычисления в точке
param.for_r_soi = 0;
%% траектория КА
savefilename = 'venus_cycle_3.mat';
load(savefilename)
for k = 1:N_count_1

    if checked(k)>0
        continue
    end
    disp(k)
    checked(k) = 1;
    %save(savefilename)
    param.t_start = param.t_start_zero+delta_t_starts(k);
    
    st.t = param.t_start;
    st.planet = 'Earth';
    st.mode = 'Simple';
    
    [earth_r_0, earth_v_0]=planetModel(st);
    earth_r_0=earth_r_0'*1e+03;
    earth_v_0=earth_v_0'*1e+03;
    
    % Исходные r, v, m (7 переменных)
    r0 = earth_r_0;  % нач. радиус (пример — ~ORB высота)
    v0 = earth_v_0;   % нач. скорость
    mUsed0 = 0;           % израсходованная масса на t=0 (обычно 0)
    
    
    %tspan = [0, param.t_end_initial*param.T_earth];  % интервал времени
    
    
    %
    A = [];
    b = [];
    Aeq = [];
    beq = [];
    
    % Точное решение для juliandate(2032,11,1)из venus.m
    r0_initial = 1.0e+11 * [
       1.115126024104636
       0.978043194633004
      -0.000001495802959];
    
    v0_initial = 1.0e+04 * [
      -2.013314219880796
       2.229333032255102
      -0.000121129535643];
    
    dv0_initial = 1.0e+03 *[
    
       0.868230970580241;
      -2.271014143854942;
       1.439970480263999]/param.V_unit;
    pr0_initial = [
       13.681675488733557
       8.846703256008732
      30.518405272177390]; 
    pm0_initial = 94.291739932368742;
    t_end_initial = 1.070587262650349;
    
    R = calculateRotMatrix(r0',v0');
    R_ini = calculateRotMatrix(r0_initial',v0_initial');
    R_total = R^-1*R_ini;
    R_total_2 = R_total'^-1;
    pr0 = R_total*pr0_initial;
    dv0 = R_total_2*dv0_initial;
    pv0 = [0; 0; 0];
    Z0 = [dv0; pr0; pm0_initial; t_end_initial; 0];
    pm0 = pm0_initial;
    param.Y0 = [r0; v0; mUsed0; pr0; pv0; pm0]; %для интегрирования
    
    lb = -ones(1,length(Z0));
    ub = ones(1,length(Z0));
    
    %Начальная отлётная скорость
    lb(1:3)=-4000;
    ub(1:3)=+4000;
    
    %Начальное сопряжённое положение
    lb(4:6)=-100;
    ub(4:6)=+100;
    
    %Начальная сопряжённая масса
    lb(7)=-500;
    ub(7)=500;
    
    %время перелёта
    lb(8)=0.5;
    ub(8)=1.5;
    
    %время перелёта
    lb(9)=0;
    ub(9)=0;
    %
    
    
    fun=@(X)fun2min_border(X, param);
    fun_J=@(X)fun2min_J(X, param);
    options = optimoptions('fmincon','UseParallel', true);
    options = optimoptions(options,'BarrierParamUpdate','predictor-corrector');
    options = optimoptions(options,'HessianApproximation','lbfgs');
    options = optimoptions(options, 'ScaleProblem', true);
    options = optimoptions(options, 'Display', 'off');
    options = optimoptions(options, 'OptimalityTolerance', 1e-10);
    options = optimoptions(options, 'MaxFunctionEvaluations', 1e+10);
    options = optimoptions(options, 'StepTolerance', 1e-10);
    options = optimoptions(options, 'ConstraintTolerance', 1e-10);
    options = optimoptions(options, 'MaxIterations', 250);
    options = optimoptions(options, 'FiniteDifferenceType', 'central');
    options = optimoptions(options, 'EnableFeasibilityMode', true);
    try
        ZF = fmincon(fun_J, Z0, A, b, Aeq, beq, lb, ub, fun, options);
    catch 
        ZF=Z0;
    end
    
    
    %options_fsolve = optimoptions('fsolve','Display','off');
    %fsolve_traj_fun=@(z)fsolve_traj(z,Y0,yf,param.t_start,tspan(end), param);
    %[ZF, fval] = fsolve(fsolve_traj_fun, Z0, options_fsolve);
    
    DV0=ZF(1:3)*param.V_unit;
    pr0=param.pr_scaler*ZF(4:6)/param.r_unit;
    pm0=ZF(7);
    t_end = ZF(8);
    param.Y0(4:6)=earth_v_0+DV0;
    param.Y0(8:10)=pr0;
    param.Y0(14)=pm0;
    param.Y0(15)=0;
    %
    tspan = [0,t_end*param.T_earth];  % интервал времени
    % 3) Вызываем ode15s:
    
    options = odeset('RelTol',1e-8,'AbsTol',1e-10);
    options = odeset(options, 'Events',@(s, y) eventIntegrationTrajStopM(s, y, param));
    [t_sol, Y_sol] = ode15s(@(t, Y) integrate_dmdt_optimal_withJ(t, Y, param), tspan, param.Y0, options);
    
    %положение и скорость КА
    SC_rf = Y_sol(end, 1:3);
    SC_vf = Y_sol(end, 4:6);
    mf = Y_sol(end, 7);
    
    st.t = param.t_start+tspan(end)/(3600*24);
    st.planet = param.target_body;
    st.mode = 'Simple';
    
    [target_r_f, target_v_f]=planetModel(st);
    target_r_f=target_r_f'*1e+03;
    target_v_f=target_v_f'*1e+03;
    yf = [target_r_f;target_v_f]';
    res_rf = norm(SC_rf'-target_r_f);
    res_vf = norm(SC_vf'-target_v_f);
    V_inf = sqrt(norm(DV0/1000)^2-2*398600/(929*1000));
    % 4) Разбор результатов
    % Y_sol(:,1:3)  -> компоненты r(t)
    % Y_sol(:,4:6)  -> компоненты v(t)
    % Y_sol(:,7)    -> m(t) (израсходованная масса)
    % Y_sol(:,8:10) -> lambda_r(t)
    % Y_sol(:,11:13)-> lambda_v(t)
    % Y_sol(:,14)   -> lambda_m(t)
    
    % Порог для определения точки разрыва
    threshold = 1e-5;
    threshold2 = 1e-4;
    
    % Вычисление разностей между соседними элементами
    diffs = abs(diff(Y_sol(:,7)));
    
    % Индексы, где разность превышает порог
    nonzero_derivative = diffs > threshold;
    nonzero_derivative(end+1) = nonzero_derivative(end);
    
    diffs2 = abs(diff(nonzero_derivative));
    
    % Индексы, где разность превышает порог
    break_points = find(diffs2 > threshold2);
    
    %t_active = t_sol(nonzero_derivative>0.5);
    t_sol_active = cumtrapz(t_sol, nonzero_derivative);
    active_days = 365*t_sol_active(end)/param.T_earth;
    
    
    Vhar = Y_sol(end,15)/1000;
    disp(['Невязка положения ', num2str(round(norm(res_rf)/1000,4)), ' км']);
    disp(['Подлётная скорость ', num2str(round(norm(res_vf)/1000,4)), ' км/c']);
    %disp(['Отлётная скорость ', num2str(round(norm(DV0)/1000,4)), ' км/c']);
    disp(['Характеристическая скорость ', num2str(round(Vhar,4)), ' км/с']);
    disp(['Гиперболический избыток ', num2str(round(V_inf,4)), ' км/c']);
    disp(['Расход топлива ', num2str(round(mf,4)), ' кг']);
    disp(['Время перелёта ', num2str(round(t_end,4)*365), ' суток']);
    disp(['Время работы дигателя ', num2str(round(active_days,4)), ' суток']);
    active_days_breaks = t_sol(break_points)/3600/24;
    disp(['Дата старта ', char(datetime(param.t_start,'convertfrom','juliandate','Format','dd.MM.yyyy'))])
    disp(['Дата подлёта к Венере ', char(datetime(param.t_start+tspan(end)/(3600*24),'convertfrom','juliandate','Format','dd.MM.yyyy'))])
    for i =1:length(break_points)
    disp(['Время переключения двигателя ', char(datetime(param.t_start+active_days_breaks(i),'convertfrom','juliandate','Format','dd.MM.yyyy'))])
    end
    
    
    resrf_massive(k) = norm(res_rf)/1000;%невязка положения
    revf_massive(k) = norm(res_vf)/1000;%невязка скорости
    Vhar_massive(k) = Vhar;%характеристическая скорость самого КА
    Vinf_massive(k) = V_inf;%отлётная скорость
    mf_massive(k) = mf;%расход топлива
    t_end_massive(k) = t_end*365;%время перелёта
    active_days_massive(k) = active_days;%время работы дигателя
    save(savefilename)
end

%%
figure(3);
ok_points = resrf_massive < 500 & abs(revf_massive-param.dv_target/1000) < 0.5 & Vhar_massive > 0;
ok_points_2 = ok_points & Vhar_massive <= 4.95;
scatter(delta_t_starts(ok_points),Vhar_massive(ok_points), 'k.', 'HandleVisibility','off')
grid;
deltas_short = 365*[0:10];
deltas_short(3:end) = deltas_short(3:end) + 1;
deltas_short(7:end) = deltas_short(7:end) + 1;
deltas_short(end) = deltas_short(end) + 1;
xticks(deltas_short)
dates = arrayfun(@(dt) char(datetime(param.t_start_zero + dt, ...
    'convertfrom', 'juliandate', 'Format', 'dd.MM.yyyy')), deltas_short, ...
    'UniformOutput', false);
for i=1:9
end
xticklabels(dates)
xlim([0,365*10+10])
ylabel('Характеристическая скорость перелёта, км/с')
xlabel('Дата старта')
hold on;
plot([0,365*10+10],[5.4,5.4], 'k--', 'DisplayName','Весь запас хар. скорости')
plot([0,365*10+10],[5.4,5.4]-0.45, 'k-.', 'DisplayName','Запас хар. скорости за вычетом последующей скрутки')
hold off;
legend;
set(gca,'fontsize', 11)
%%
figure(4);
scatter(delta_t_starts(ok_points_2),t_end_massive(ok_points_2), 'k.')
grid;
deltas_short = 365*[0:10];
deltas_short(3:end) = deltas_short(3:end) + 1;
deltas_short(7:end) = deltas_short(7:end) + 1;
deltas_short(end) = deltas_short(end) + 1;
xticks(deltas_short)
dates = arrayfun(@(dt) char(datetime(param.t_start_zero + dt, ...
    'convertfrom', 'juliandate', 'Format', 'dd.MM.yyyy')), deltas_short, ...
    'UniformOutput', false);
for i=1:9
end
xticklabels(dates)
xlim([0,365*10+10])
ylabel('Продолжительность перелёта, сутки')
xlabel('Дата старта')
set(gca,'fontsize', 11)
%%
figure(5);
ok_points = resrf_massive < 500 & abs(revf_massive-param.dv_target/1000) < 100 & Vhar_massive > 0;
scatter(delta_t_starts(ok_points_2),Vinf_massive(ok_points_2), 'k.')
grid;
deltas_short = 365*[0:10];
deltas_short(3:end) = deltas_short(3:end) + 1;
deltas_short(7:end) = deltas_short(7:end) + 1;
deltas_short(end) = deltas_short(end) + 1;
xticks(deltas_short)
dates = arrayfun(@(dt) char(datetime(param.t_start_zero + dt, ...
    'convertfrom', 'juliandate', 'Format', 'dd.MM.yyyy')), deltas_short, ...
    'UniformOutput', false);
for i=1:9
end
xticklabels(dates)
xlim([0,365*10+10])
ylabel('Гиперболический избыток, км/с')
xlabel('Дата старта')
set(gca,'fontsize', 11)
%%
figure(6);
st.t = param.t_start+linspace(0, 365.256363004, 100)';
st.planet = 'Earth';
st.mode = 'Simple';

[earth_r, earth_v]=planetModel(st);
earth_r=earth_r'*1e+03;
earth_v=earth_v'*1e+03;



st.t = param.t_start+linspace(0, 224.7, 100)';
st.planet = param.target_body;
st.mode = 'Simple';

[Venus_r, Venus_v]=planetModel(st);
Venus_r=Venus_r'*1e+03;
Venus_v=Venus_v'*1e+03;


st.t = param.t_start;
st.planet = param.target_body;
st.mode = 'Simple';

[Venus_r_0, Venus_v_0]=planetModel(st);
Venus_r_0=Venus_r_0'*1e+03;
Venus_v_0=Venus_v_0'*1e+03;


%%
figure(6)
plot3(earth_r(1,:)/r_unit,earth_r(2,:)/r_unit,earth_r(3,:)/r_unit, 'k--', 'LineWidth',1.5, 'DisplayName','Орбита Земли')
hold on
plot3(earth_r_0(1)/r_unit,earth_r_0(2)/r_unit,earth_r_0(3)/r_unit, 'bO', 'LineWidth',1.5, 'HandleVisibility','off')
plot3(Venus_r(1,:)/r_unit,Venus_r(2,:)/r_unit,Venus_r(3,:)/r_unit, '-.k', 'LineWidth',1.5, 'DisplayName','Орбита Венеры')
%plot3(Venus_r_0(1)/r_unit,Venus_r_0(2)/r_unit,Venus_r_0(3)/r_unit, 'kO', 'LineWidth',1.5, 'HandleVisibility','off')
plot3(Y_sol(1,1)/r_unit,Y_sol(1,2)/r_unit,Y_sol(1,3)/r_unit, 'magenta', 'LineWidth',1.5, 'DisplayName','Активный участок')
plot3(Y_sol(1,1)/r_unit,Y_sol(1,2)/r_unit,Y_sol(1,3)/r_unit, 'cyan', 'LineWidth',1.5, 'DisplayName','Пассивный участок')


color_count = nonzero_derivative(1);
for i = 1:length(break_points) + 1
    if color_count == 0
        color = 'cyan';
        disp_name = 'Пассивный участок';
    else
        color = 'magenta';
        disp_name = 'Активный участок';
    end
    color_count = ~color_count;
    if length(break_points) == 0
        plot3(Y_sol(1:end,1)/r_unit, Y_sol(1:end,2)/r_unit, Y_sol(1:end,3)/r_unit, color, 'LineWidth', 2, 'DisplayName',disp_name);
    else
        if i == 1
            % Первая часть до первого разрыва
            plot3(Y_sol(1:break_points(i),1)/r_unit, Y_sol(1:break_points(i),2)/r_unit, Y_sol(1:break_points(i),3)/r_unit, color, 'LineWidth', 2, 'HandleVisibility','off');
        elseif i == length(break_points) + 1
            % Последняя часть после последнего разрыва
            plot3(Y_sol(break_points(i-1)+1:end, 1)/r_unit, Y_sol(break_points(i-1)+1:end, 2)/r_unit, Y_sol(break_points(i-1)+1:end, 3)/r_unit, color, 'LineWidth', 2, 'HandleVisibility','off');
        else
            % Промежуточные части
            plot3(Y_sol(break_points(i-1)+1:break_points(i), 1)/r_unit, Y_sol(break_points(i-1)+1:break_points(i), 2)/r_unit,Y_sol(break_points(i-1)+1:break_points(i), 3)/r_unit, color, 'LineWidth', 2, 'HandleVisibility','off');
        end
    end
    
end
plot3(target_r_f(1)/r_unit,target_r_f(2)/r_unit,target_r_f(3)/r_unit, 'rO', 'LineWidth',1.5, 'HandleVisibility','off')
plot3(Y_sol(end,1)/r_unit,Y_sol(end,2)/r_unit,Y_sol(end,3)/r_unit, 'kO', 'LineWidth',1.5, 'HandleVisibility','off')
hold off;
grid;
axis equal;
xlabel('x, a.e.')
ylabel('y, a.e.')
zlabel('z, a.e.')
legend;
view(0,90)
ax = gca;
ax.XAxisLocation = 'origin';
ax.YAxisLocation = 'origin';
