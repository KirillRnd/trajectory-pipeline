clear all
clc

% fundamental constants
% ---------------------
G=6.67384*1e-20;        % km^3/s^2/kg
AU=149597841;           % km
DAY=86400;              % s
RAD=180/pi;             % deg
% ---------------------

% masses of celectial bodies (in 10^24 kg)
% ----------------------------------------
m_S=1.9885*10^6;        % mass of the Sun
m_V=4.8676;             % mass of Venus
m_E=5.9722;             % mass of the Earth
m_M=0.64185;            % mass of Mars
m_Moon=0.07348;         % mass of the Moon
% ----------------------------------------

% gravitational parameters
% ------------------------
GM_S=G*m_S*10^24/AU^3*DAY^2;  % AU^3/days^2
GM_E=G*m_E*10^24/AU^3*DAY^2;  % AU^3/days^2
% ------------------------

% planets' best-fit elements and their centennial rates wrt the mean ecliptic and equinox of J2000
% (errors are up to 100" for the inner planets and up to 2000" for the outer planets)
% ------------------------------------------------------------------------------------------------
% a - semimajor axis [AU] (rate - in AU/Cy)
% e - eccentricity (rate - in 1/Cy)
% inc - inclination [deg] (rate - in deg/Cy)
% Om - longitude of the ascending node [deg] (rate - in deg/Cy)
% om - longitude of perihelion [deg] (rate - in deg/Cy)
% lam - mean longitude [deg] (rate - in deg/Cy)
% -------------------------------------------------------------
% Venus
% -------------------------------------------------------------
el_V=[0.72332102  0.00676399  3.39777545  76.67261496 131.76755713   181.97970850;
     -0.00000026 -0.00005107  0.00043494  -0.27274174   0.05679648 58517.81560260];
% -------------------------------------------------------------
% Earth+Moon barycenter
% -------------------------------------------------------------
el_E=[1.00000018  0.01673163 -0.00054346  -5.11260389 102.93005885   100.46691572;
     -0.00000003 -0.00003661 -0.01337178  -0.24123856   0.31795260 35999.37306329];
% el_E=[1.0 0.0 0.0 0.0 0.0 0.0;
%       0.0 0.0 0.0 0.0 0.0 0.0];
% -------------------------------------------------------------
% Mars
% -------------------------------------------------------------
el_M=[1.5 0.0 0.0 0.0 0.0 0.0;
      0.0 0.0 0.0 0.0 0.0 0.0];
% -------------------------------------------------------------

% elements and centennial rates of natural and artificial satellites
% ------------------------------------------------------------------
% Moon
% ------------------------------------------------------------------
el_Moon=[384400/AU 0.0554 5.16 125.08 83.23 218.50;
        0.00382/AU 0 0 -360*100/18.600 360*100/8.851 13.287629*36525];
% ------------------------------------------------------------------
% Geostationary satellite
% ------------------------------------------------------------------
el_GEO=[42164/AU 0 23.44 0 0 0;
        0 0 0 0 0 0];
%-------------------------------------------------------------------

% parameters of the spacecraft
% ----------------------------
m_SC=400;           % kg - initial mass of the spacecraft
T_max=0.332;        % N - maximum value of thrust
I_sp=1500;          % s - thruster's specific impulse
N=5400;             % W - electric power
eta=0.5;            % electrical efficiency
% ----------------------------

% structures of planets' parameters
% ---------------------------------
S=struct('name','Sun','mass',m_S,'GM',GM_S);
V=struct('name','Venus','mass',m_V,'elements',el_E);
E=struct('name','Earth','mass',m_E,'GM',GM_E,'elements',el_E);
M=struct('name','Mars','mass',m_M,'elements',el_M);
% ---------------------------------

% structures of natural and artificial satellites' parameters
% -----------------------------------------------------------
Moon=struct('name','Moon','mass',m_Moon,'elements',el_Moon);
GEO=struct('name','GEO','mass',m_SC,'elements',el_GEO);
% -----------------------------------------------------------

% structure of spacecraft parameters
% ----------------------------------
SC=struct('name','spacecraft','mass',m_SC,'max_thrust',T_max,'spec_imp',I_sp,'power',N,'el_eff',eta);
% ----------------------------------

% maximum value of hyperbolic excess velocity
% -------------------------------------------
vinf_max=0;         % km/s
% -------------------------------------------

% choosing the start and finish times
% -----------------------------------
time0=struct('year',2022,'month',06,'day',23,'hour',12,'minute',00,'second',00);
timef=struct('year',2023,'month',08,'day',04,'hour',12,'minute',00,'second',00);
% -----------------------------------

% recalculating to Julian date (MJD)
% ----------------------------------
t0=calc_JD(time0)-2451545;       % start time (in days) since the J2000 epoch
tf=calc_JD(timef)-2451545;       % finish time (in days) since the J2000 epoch
% ----------------------------------

% choosing the central body
% -------------------------
central_body=S;
% -------------------------

% choosing the initial and target objects
% ---------------------------------------
initial_object=E;
target_object=M;
% ---------------------------------------

% initial and target objects' keplerian elements (of start and finish date, respectively)
% ---------------------------------------------------------------------------------------
el_0=initial_object.elements(1,:)+t0*initial_object.elements(2,:)/36525;
% tf=t0+6.5/sqrt(central_body.GM/el_0(1)^3);
el_f=target_object.elements(1,:)+tf*target_object.elements(2,:)/36525;
el_0(6)=el_0(6)-360*floor(el_0(6)/360);
el_f(6)=el_f(6)-360*floor(el_f(6)/360);
% ---------------------------------------------------------------------------------------

% initial and target objects' equinoctial elements (of start and finish date, respectively)
% -----------------------------------------------------------------------------------------
% a = a [AU]
% k = e*cos(om)
% h = e*sin(om)
% q = tan(inc/2)*cos(om-Om)
% p = tan(inc/2)*sin(om-Om)
% lam = lam [rad]
% -----------------------------------------------------------------------------------------
eq_el_0=[el_0(1) el_0(2)*cos(el_0(5)/RAD) el_0(2)*sin(el_0(5)/RAD) tan(el_0(3)/RAD/2)*cos((el_0(5)-el_0(4))/RAD) tan(el_0(3)/RAD/2)*sin((el_0(5)-el_0(4))/RAD) el_0(6)/RAD];
eq_el_f=[el_f(1) el_f(2)*cos(el_f(5)/RAD) el_f(2)*sin(el_f(5)/RAD) tan(el_f(3)/RAD/2)*cos((el_0(5)-el_0(4))/RAD) tan(el_f(3)/RAD/2)*sin((el_0(5)-el_0(4))/RAD) el_f(6)/RAD];
% -----------------------------------------------------------------------------------------

% initial and target objects' position and velocity at the start and finish moments, respectively
% -----------------------------------------------------------------------------------------------
[r0,v0]=eq2cart(eq_el_0,central_body.GM);
[rf,vf]=eq2cart(eq_el_f,central_body.GM);
% -----------------------------------------------------------------------------------------------

% choosing the number of revolutions and preparing for GM continuation procedure
% ------------------------------------------------------------------------------
dM0=sqrt(central_body.GM/el_0(1)^3)*(tf-t0);
Nrev0=floor(dM0/2/pi);
Nrev=1;
dM=atan2(rf(2),rf(1))-atan2(r0(2),r0(1));
mu0=((dM+Nrev*2*pi)/(tf-t0))^2*el_0(1)^3/central_body.GM;
% ------------------------------------------------------------------------------

% trajectory optimization
% -----------------------
[t,u,w,r,p0,dv,J]=indir_opt(mu0,central_body.GM,t0,tf,r0,v0,rf,vf,vinf_max*DAY/AU);
plot(t-t0,u(:,1)*10^6*AU/DAY^2,'k')
xlabel('Время, дни')
ylabel('Управляющее ускорение, мм/с^2')
xlim([0 tf-t0])
% ------------------------

% plotting the optimal trajectory (in ecliptic projection) and control acceleration
% ---------------------------------------------------------------------------------
figure
plot(r(:,1)*AU/10^6,r(:,2)*AU/10^6,'k','LineWidth',2)
hold on
plot_orb(eq_el_0.*[AU/10^6 1 1 1 1 1],central_body.GM*(AU/10^6)^3*(1+initial_object.mass/central_body.mass))
hold on
plot_orb(eq_el_f.*[AU/10^6 1 1 1 1 1],central_body.GM*(AU/10^6)^3*(1+target_object.mass/central_body.mass))
xlabel('X, млн.км')
ylabel('Y, млн.км')
xlim([-300 300])
ylim([-300 300])
axis equal
% -------------------------------------------------------------------------

% saving the solution along with the sun vector
% ---------------------------------------------
Nt=size(t,1);
sol=zeros(Nt,8);
sunvec=zeros(Nt,3);

if isequal(central_body,S)==0
    elem=zeros(Nt,6);
    eqelem=zeros(Nt,6);
    r_cb=zeros(Nt,3);
    v_cb=zeros(Nt,3);
    r_SC=zeros(Nt,3);
end

for i=1:Nt
    sol(i,1)=t(i)-t0;
    sol(i,2:4)=r(i,1:3)*AU;
    sol(i,5:7)=w(i,1:3)/norm(w(i,1:3));
    sol(i,8)=norm(w(i,1:3))*AU*10^6/DAY^2;
    
    if isequal(central_body,S)==0
        elem(i,:)=central_body.elements(1,:)+central_body.elements(2,:)*t(i)/36525;
        eqelem(i,:)=[elem(i,1) elem(i,2)*cos(elem(i,5)/RAD) elem(i,2)*sin(elem(i,5)/RAD) tan(elem(i,3)/RAD/2)*cos((elem(i,5)-elem(i,4))/RAD) tan(elem(i,3)/RAD/2)*sin((elem(i,5)-elem(i,4))/RAD) elem(i,6)/RAD];
        [r_cb(i,:),v_cb(i,:)]=eq2cart(eqelem(i,:),S.GM);
        
        if isequal(central_body,E)==1
            r_SC(i,:)=E.mass/(E.mass+Moon.mass)*r(i,:);
        else
            r_SC(i,:)=r(i,:);
        end
        
        sunvec(i,:)=-(r_cb(i,:)+r_SC(i,:))/norm(r_cb(i,:)+r_SC(i,:));
    else
        sunvec(i,:)=-r(i,:)/norm(r(i,:));
    end
end

% save moon.mat sol sunvec
% ---------------------------------------------

% modeling the discretization and implementation errors
% -----------------------------------------------------
% A=load('thruster_rand.mat');
% e=A.thruster_rand(:,2:4);
% 
% for i=1:Nt
%     w(i,:)=u(i,1)*e(i,:);
% end
% 
% rerr=zeros(Nt,3);
% rerr(1,:)=r0;
% verr=zeros(Nt,3);
% verr(1,:)=v0;
% 
% for i=2:Nt
%     [t_temp,x_temp]=ode45(@(t,y)right_side(central_body.GM,t,y),[t(i-1),t(i)],[rerr(i-1,:)'; verr(i-1,:)'; zeros(6,1)]);
%     rerr(i,:)=x_temp(size(t_temp,1),1:3)+(w(i-1,:)+w(i,:))/2*(t(i)-t(i-1))^2/2;
%     verr(i,:)=x_temp(size(t_temp,1),4:6)+(w(i-1,:)+w(i,:))/2*(t(i)-t(i-1));
%     i
% end
% -----------------------------------------------------

% plotting the position error components and magnitude
% ----------------------------------------------------
% days=7;
% T=days*24*4;
% figure
% plot(t(1:T)-t0,(rerr(1:T,1)-r(1:T,1))*AU,'k','LineWidth',1)
% xlabel('Время, дни')
% ylabel('Ошибка по оси X, км')
% xlim([0 days])
% ylim([-1000 1000])
% figure
% plot(t(1:T)-t0,(rerr(1:T,2)-r(1:T,2))*AU,'k','LineWidth',1)
% xlabel('Время, дни')
% ylabel('Ошибка по оси Y, км')
% xlim([0 days])
% ylim([-1000 1000])
% figure
% plot(t(1:T)-t0,(rerr(1:T,3)-r(1:T,3))*AU,'k','LineWidth',1)
% xlabel('Время, дни')
% ylabel('Ошибка по оси Z, км')
% xlim([0 days])
% ylim([-1000 1000])
% figure
% plot(t(1:T)-t0,sqrt((rerr(1:T,1)-r(1:T,1)).^2+(rerr(1:T,2)-r(1:T,2)).^2+(rerr(1:T,3)-r(1:T,3)).^2)*AU,'k','LineWidth',1)
% xlabel('Время, дни')
% ylabel('Ошибка в положении КА, км')
% ----------------------------------------------------