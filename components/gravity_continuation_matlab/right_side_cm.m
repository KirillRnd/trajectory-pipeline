function g = right_side_cm(mu0,mu,t0,tf,tau,r0,v0,z,rf,vf,b)

% This function defines the right side of the continuation method ode set
% -----------------------------------------------------------------------
step_z=1e-14;
step_tau=1e-10;
fz=zeros(6,6);
mutau=mu0+(1-mu0)*tau;

options=odeset('RelTol',1e-7,'AbsTol',1e-10);
[t,x]=ode45(@(t,y)right_side(mu*mutau,t,y),[t0,tf],[r0; v0*sqrt(mutau); z],options);
f=[x(size(t,1),1:3)'-rf; x(size(t,1),4:6)'-sqrt(mutau)*vf];

for k=1:6
    z_temp=z;
    z_temp(k)=z_temp(k)+step_z;
    [t_temp,x_temp]=ode45(@(t,y)right_side(mu*mutau,t,y),[t0,tf],[r0; v0*sqrt(mutau); z_temp],options);
    f_temp=[x_temp(size(t_temp,1),1:3)'-rf; x_temp(size(t_temp,1),4:6)'-sqrt(mutau)*vf];
    fz(:,k)=(f_temp-f)/step_z;
    clear t_temp x_temp f_temp
end

tau

mu_temp=mu0+(1-mu0)*(tau+step_tau);
[t_temp,x_temp]=ode45(@(t,y)right_side(mu_temp*mu,t,y),[t0,tf],[r0; v0*sqrt(mu_temp); z],options);
ftau=[(x_temp(size(t_temp,1),1:3)'-x(size(t,1),1:3)')/step_tau; (x_temp(size(t_temp,1),4:6)'-x(size(t,1),4:6)')/step_tau-1/2/sqrt(mutau)*(1-mu0)*vf];
clear t_temp x_temp
g=-fz\(b+ftau);

end