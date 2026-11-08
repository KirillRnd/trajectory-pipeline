%параметры космического аппарата и некоторые константы
clc;
clear;
standart_parameters

param.dv_target = 1000*sqrt(2*324859/616000);
param.r_planet = 0.723327331758308*r_unit;
param.mug = 324859*(10^(3*3)); %гравитационный параметр
param.r_SOI = 616000;
%%
rf_per = (6051.8+400);
rf_apo = (6051.8+30000);
a = (rf_per+rf_apo)/2;
v_per = sqrt(param.mug/(10^(3*3)))*sqrt(2/rf_per - 1/a);
v_apo = sqrt(param.mug/(10^(3*3)))*sqrt(2/rf_apo - 1/a);
%% параметры входа

rf = (6051.8+400)*1000;

radius = (6051.8);
phi = -pi/4;
r0 = 616000*1000*[cos(phi), sin(phi), 0];
v0 = [0, param.dv_target, 0];
vf = sqrt(param.mug/rf);
m0 = 34.683; 

r0 = [rf, 0, 0];
%v0 = [0, 1.3025*vf, 0];
v0 = [0, v_per*1000, 0];

m0 = 64; 
m_avaliable = m0-34.683;
t0 = 0.9798*param.T_earth;
%y0 = [r0,v0,m0];


[a,eMag,iMag,O,o,nu,truLon,argLat,lonPer,p] =  rv2orb(r0'/1000,v0'/1000,param.mug/(10^(3*3)));
[p,ex,ey,ix,iy,L] = orb2equintoctial(p,eMag,iMag,O,lonPer,nu);
y0 = [p;ex;ey;ix;iy;L;m0];
T = 2*pi*sqrt(a^3/(param.mug/(10^(3*3))));
%t_end = T*37500;
param.control_type = 2;
param.angle_function = @(e)(pi/2)*(0.65*e+1);
t_end = T*5000;
param.angle = 2*pi;
%%
%tspan = [t0+t_end*param.T_earth,t0];  % интервал времени
tspan = linspace(t0+t_end,t0,100000);  % интервал времени
%tspan = [t0,t0+t_end*param.T_earth];  % интервал времени
% 3) Вызываем ode15s:

options = odeset('RelTol',1e-8,'AbsTol',1e-10);
options = odeset(options, 'Events',@(s, y) eventIntegrationTrajStopRApo(s, y, param));
[t_sol, Y_sol] = ode15s(@(t, Y) integrate_equinoctial(t, Y, param), tspan, y0, options);

traj = arrayfun(@(p,ex,ey,ix,iy,L) equitoctial2decart([p;ex;ey;ix;iy;L], param.mug/(10^(3*3))),...
    Y_sol(:, 1),Y_sol(:, 2),Y_sol(:, 3),Y_sol(:, 4),Y_sol(:, 5),Y_sol(:, 6),'UniformOutput',false);
traj = cell2mat(traj')';
%положение и скорость КА
SC_rf = traj(end, 1:3);
SC_vf = traj(end, 4:6);
mf = Y_sol(end, 7);
%%
[a,eMag,iMag,O,o,nu,truLon,argLat,lonPer,p] =  rv2orb(SC_rf',SC_vf',param.mug/(10^(3*3)));
h = (param.mug/(10^(3*3)))*(eMag^2-1)/p;
%disp(['Финальная высота ', num2str(round(norm(SC_rf)/1000,4)), ' км']);
disp(['Кеплерова энергия ', num2str(round(h,4))]);
disp(['Расход топлива ', num2str(round(mf,4)-m0), ' кг']);
disp(['Время перелёта ', num2str(365*round((t_sol(1)-t_sol(end))/param.T_earth,4)), ' суток']);

[a,eMag,iMag,O,o,nu,truLon,argLat,lonPer,p] =  rv2orb(r0'/1000,v0'/1000,param.mug/(10^(3*3)));
disp(['Высота перицентра ', num2str(round(a*(1-eMag),4)-6051.8), ' км']);
disp(['Высота апоцентра ', num2str(round(a*(1+eMag),4)-6051.8), ' км']);
e = sqrt(Y_sol(:, 2).^2+Y_sol(:, 3).^2);
%%
figure(1)
L_local = mod(Y_sol(:, 6), 2*pi);
%angle_fun = (pi/2)*(0.65*e+1);
angle_fun = pi;
angles = abs(L_local) < angle_fun | abs(L_local) > 2*pi-angle_fun;
diffs = abs(diff(angles));
threshold = 0.5;
% Индексы, где разность превышает порог
break_points = find(diffs > threshold);

t_sol_active = cumtrapz(t_sol, angles);
active_days = -365*t_sol_active(end)/param.T_earth;
disp(['Машинное время ', num2str(active_days,4), ' суток']);
plot3(traj(1,1)/radius,traj(1,2)/radius,traj(1,3)/radius, 'magenta', 'LineWidth',1.5, 'DisplayName','Активный участок')
hold on;
plot3(traj(1,1)/radius,traj(1,2)/radius,traj(1,3)/radius, 'cyan', 'LineWidth',1.5, 'DisplayName','Пассивный участок')


color_count = angles(1);
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
        plot3(traj(1:end,1)/radius, traj(1:end,2)/radius, traj(1:end,3)/radius, color, 'LineWidth', 1.5);
    else
        if i == 1
            % Первая часть до первого разрыва
            plot3(traj(1:break_points(i),1)/radius, traj(1:break_points(i),2)/radius, traj(1:break_points(i),3)/radius, color, 'LineWidth', 1.5, 'HandleVisibility','off');
        elseif i == length(break_points) + 1
            % Последняя часть после последнего разрыва
            plot3(traj(break_points(i-1)+1:end, 1)/radius, traj(break_points(i-1)+1:end, 2)/radius, traj(break_points(i-1)+1:end, 3)/radius, color, 'LineWidth', 1.5, 'HandleVisibility','off');
        else
            % Промежуточные части
            plot3(traj(break_points(i-1)+1:break_points(i), 1)/radius, traj(break_points(i-1)+1:break_points(i), 2)/radius,traj(break_points(i-1)+1:break_points(i), 3)/radius, color, 'LineWidth', 1.5, 'HandleVisibility','off');
        end
    end

end

hold off;
grid;
axis equal;
xlabel('x, радиусы Венеры')
ylabel('y, радиусы Венеры')
zlabel('z, радиусы Венеры')
%xlim([-600,10])
legend;
view(0,90)
ax = gca;
ax.XAxisLocation = 'origin';
ax.YAxisLocation = 'origin';
