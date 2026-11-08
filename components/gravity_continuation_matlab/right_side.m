function f = right_side(mu,t,x)

% This function defines the right side of the state/costate ode set
% -----------------------------------------------------------------
f=zeros(12,1);

r=x(1:3);
v=x(4:6);
p=x(7:9);
vp=x(10:12);

nr=norm(r);
grad=mu/nr^3*[3*r(1)^2/nr^2-1 3*r(1)*r(2)/nr^2 3*r(1)*r(3)/nr^2;
              3*r(2)*r(1)/nr^2 3*r(2)^2/nr^2-1 3*r(2)*r(3)/nr^2;
              3*r(3)*r(1)/nr^2 3*r(3)*r(2)/nr^2 3*r(3)^2/nr^2-1];

f(1:3)=v;
f(4:6)=-mu/nr^3*r+p;
f(7:9)=vp;
f(10:12)=grad*p;

end