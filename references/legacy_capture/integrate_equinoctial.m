function dydt = integrate_equinoctial(t,y,param)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
% Функция для ode15s: возвращает правые части фазовых и сопряжённых уравнений.


%--- Разбираем состояния ---
p = y(1);
ex = y(2);
ey = y(3);
ix = y(4);
iy = y(5);
L = y(6);
mUsed = y(7);   % уже израсходованная масса

mug         = param.mug/(10^(3*3));
%mug         = param.mug;
m0         = param.m0;
%расстояние до Солнца считаем константой
r_planet   = param.r_planet;
u          = u_from_rt(t,r_planet,param);
gamma_max  = gamma_max_from_rt(t,r_planet,param);

% Текущая "актуальная" масса аппарата (m0 - mUsed)
mass = m0 - mUsed;
A = (gamma_max*u/mass)/1000; %км/с2
%----------------- Фазовые уравнения (1)–(3) -----------------
%a = [S;T;W];
phi = 1 + ix^2 + iy^2;
eta = ix*sin(L) - iy*cos(L);
sigma = 1 + ex*cos(L) + ey*sin(L);

e = sqrt(ex^2+ey^2);

L_local = mod(L, 2*pi);
%angle = param.angle;
angle = param.angle_function(e);

if abs(L_local) < angle || abs(L_local) > 2*pi-angle

    %k = (1+1/sigma)*sin(L_local)/cos(L_local);
    %S = -a_reactive*k/(1+k^2);
    %T = -sqrt(a_reactive^2+S^2);

    k1=sin(L);
    k2=((1+1/sigma)*cos(L)+ex/sigma);
    k = sqrt(k1^2+k2^2);
    if param.control_type == 1
        S = -A*k1/k; %нормальная тяга
        T = -A*k2/k; %тангенциальная тяга
    else
        S = 0; %нормальная тяга
        T = -A; %тангенциальная тяга
    end
    W = 0; %бинормальная тяга
else
    if param.control_type == 2
        S = 0; %нормальная тяга
        T = -A; %тангенциальная тяга
        W = 0; %бинормальная тяга
    else
        S = 0; %нормальная тяга
        T = 0; %тангенциальная тяга
        W = 0; %бинормальная тяга
        gamma_max = 0;
    end
end

%вспомогательные выражения


%производные по времени
dpdt  = sqrt(p/mug)*(2*p/sigma)*T;
dexdt = sqrt(p/mug)*( sin(L)*S + ((1+1/sigma)*cos(L)+ex/sigma)*T + (-ey*eta/sigma)*W);
deydt = sqrt(p/mug)*(-cos(L)*S + ((1+1/sigma)*sin(L)+ey/sigma)*T +  (ex*eta/sigma)*W);
dixdt = sqrt(p/mug)*(phi*cos(L)/(2*sigma))*W;
diydt = sqrt(p/mug)*(phi*sin(L)/(2*sigma))*W;
dLdt  = sqrt(mug/p)*(sigma^2/p)+sqrt(p/mug)*(eta/sigma)*W;
dmdt = param.m_compensation*gamma_max;

%----------------- Собираем всё в dYdt -----------------
dydt = zeros(size(y));
dydt(1)   = dpdt;
dydt(2)   = dexdt;
dydt(3)   = deydt;
dydt(4)   = dixdt;
dydt(5)   = diydt;
dydt(6)   = dLdt;
dydt(7)   = dmdt;
end