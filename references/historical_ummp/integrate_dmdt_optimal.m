function dydt = integrate_dmdt_optimal(t,y,param)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
% Функция для ode15s: возвращает правые части фазовых и сопряжённых уравнений.


%--- Разбираем состояния ---
r  = y(1:3);    % радиус-вектор
v  = y(4:6);    % скорость
mUsed = y(7);   % уже израсходованная масса

pr = y(8:10);   % lambda_r
pv = y(11:13);  % lambda_v
pm = y(14);     % lambda_m

mug         = param.mug;
m0         = param.m0;
u          = u_from_rt(t,r,param);
gamma_max  = gamma_max_from_rt(t,r,param);

% Текущая "актуальная" масса аппарата (m0 - mUsed)
mass = m0 - mUsed;

%------------------- Управление e^*(t) -------------------
% Если ||lv||=0, то e^*(t) в гамильтониане не влияет, берём любое, пусть [0;0;0].
pv_norm = norm(pv);
if pv_norm < 1e-12
    e_star = [0; 0; 0];
else
    e_star = pv / pv_norm;
end

%------------------- Управление gamma^*(t) по S(t) -------------------
% The optimized fuel flow is the compensated flow
% mUsed_dot = k_m*gamma.  Therefore the complete fuel term in the
% switching function must contain the same compensation factor.
% S(t) = k_m*(1 + lm) - [u/(m0 - mUsed)] * (lv·e_star).
S = param.m_compensation * (1 + pm) ...
    - (u / mass) * dot(pv, e_star);

% bang–bang (при S~0 возможен "сингулярный" случай — здесь для простоты
% оставим gamma=0 при |S|<tol, но в реальном коде возможно другое правило).
epsTol = 1e-8;
if S > epsTol
    gamma_star = 0;
elseif S < -epsTol
    gamma_star = gamma_max;
else
    % Сингулярный или "пограничный" случай S=0
    gamma_star = 0;
end

%----------------- Фазовые уравнения (1)–(3) -----------------
% dr/dt = v
drdt = v;
% dv/dt = -mu*r/||r||^3 - [gamma*u/(m0 - mUsed)] * e_star
r_norm = norm(r);
dvdt = -mug*r/(r_norm^3) - (gamma_star*u/mass)*e_star;
% dmUsed/dt = gamma
dmdt = param.m_compensation*gamma_star;

%----------------- Сопряжённые уравнения (4)–(6) -----------------

% (4) d(lambda_r)/dt = mu * grad_r[ lv · (r / ||r||^3 ) ]
%     grad_r( (lv·r)/r_norm^3 ) = lv/r_norm^3 - 3*( (lv·r)/r_norm^5 ) * r
pv_dot_r = dot(pv, r);
pr_grad = pv/(r_norm^3) - 3*(pv_dot_r)/(r_norm^5)*r;
dprdt   = mug * pr_grad;

% (5) d(lambda_v)/dt = -lr
dpvdt = -pr;

% (6) d(lambda_m)/dt = [gamma_star*u/(m0 - mUsed)^2] * (lv·e_star)
dpmdt = (gamma_star * u / (mass^2)) * dot(pv, e_star);

%----------------- Собираем всё в dYdt -----------------
dydt = zeros(size(y));
dydt(1:3)   = drdt;
dydt(4:6)   = dvdt;
dydt(7)     = dmdt;
dydt(8:10)  = dprdt;
dydt(11:13) = dpvdt;
dydt(14)    = dpmdt;
%dydt(15)    = gamma_star*u;
end
