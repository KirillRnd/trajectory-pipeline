function [t,u,w,r,p0,dv,J] = indir_opt(mu0,mu,t0,tf,r0,v0,rf,vf,vinf_max)

% This function implements the indirect trajectory optimization by applying the continuation method
% -------------------------------------------------------------------------------------------------
v0=v0*(1+vinf_max/norm(v0));
z0=zeros(6,1);

options1=odeset('RelTol',1e-7,'AbsTol',1e-10,'MaxStep',0.05);
options2=odeset('RelTol',1e-11,'AbsTol',1e-14);

[t,x]=ode45(@(t,y)right_side(mu0*mu,t,y),[t0,tf],[r0; v0*sqrt(mu0); z0],options2);
b=[x(size(t,1),1:3)'-rf; x(size(t,1),4:6)'-sqrt(mu0)*vf];

[tau,z]=ode113(@(tau,z)right_side_cm(mu0,mu,t0,tf,tau,r0,v0,z,rf,vf,b),[0,1],z0,options1);
sol=ode45(@(t,y)right_side(mu,t,y),[t0,tf],[r0; v0; z(size(tau,1),:)'],options2);
t_temp=linspace(t0,tf,(tf-t0)*24*4+1);
x_temp=deval(sol,t_temp);
t=t_temp';
x=x_temp';

r=zeros(size(t,1),3);
u=zeros(size(t,1),3);
w=zeros(size(t,1),3);
p0=z(size(tau,1),:)';
dv=0;
J=0;

for n=1:size(t,1)
    r(n,1:3)=x(n,1:3);
    u(n,1)=sqrt(x(n,7)^2+x(n,8)^2+x(n,9)^2);
    w(n,1:3)=x(n,7:9);    
    radial=x(n,1:3)/norm(x(n,1:3));
    normal=cross(x(n,4:6),radial)/norm(cross(x(n,4:6),radial));
    transv=cross(normal,radial);
    pnorm=normal*dot(x(n,7:9),normal);
    u(n,2)=pi/2-acos(dot(x(n,7:9),normal)/norm(x(n,7:9)));
    u(n,3)=asin(sqrt(1-(dot(x(n,7:9)-pnorm,transv)/norm(x(n,7:9)-pnorm))^2));    
end

for n=1:size(t,1)-1
    dv=dv+(u(n,1)+u(n+1,1))/2*(t(n+1)-t(n));
    J=J+(u(n,1)^2+u(n+1,1)^2)/2*(t(n+1)-t(n));
end

end