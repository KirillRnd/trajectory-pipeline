function [r,v] = eq2cart(eq_el,mu)

% This function transforms the equinoctial elements to the Cartesian position and velocity
% ----------------------------------------------------------------------------------------
f=[1+eq_el(4)^2-eq_el(5)^2; 2*eq_el(4)*eq_el(5); -2*eq_el(5)]/(1+eq_el(4)^2+eq_el(5)^2);
g=[2*eq_el(4)*eq_el(5); 1-eq_el(4)^2+eq_el(5)^2; 2*eq_el(4)]/(1+eq_el(4)^2+eq_el(5)^2);

F=eq_el(6);

while abs((eq_el(6)-F+eq_el(2)*sin(F)-eq_el(3)*cos(F))/(1-eq_el(2)*cos(F)-eq_el(3)*sin(F)))>1e-13
    F=F+(eq_el(6)-F+eq_el(2)*sin(F)-eq_el(3)*cos(F))/(1-eq_el(2)*cos(F)-eq_el(3)*sin(F));
end

n=sqrt(mu/eq_el(1)^3);
b=1/(1+sqrt(1-eq_el(2)^2-eq_el(3)^2));
cosL=((1-eq_el(3)^2*b)*cos(F)+eq_el(2)*eq_el(3)*b*sin(F)-eq_el(2))/(1-eq_el(2)*cos(F)-eq_el(3)*sin(F));
sinL=((1-eq_el(2)^2*b)*sin(F)+eq_el(2)*eq_el(3)*b*cos(F)-eq_el(3))/(1-eq_el(2)*cos(F)-eq_el(3)*sin(F));

X=eq_el(1)*((1-eq_el(3)^2*b)*cos(F)+eq_el(2)*eq_el(3)*b*sin(F)-eq_el(2));
Y=eq_el(1)*((1-eq_el(2)^2*b)*sin(F)+eq_el(2)*eq_el(3)*b*cos(F)-eq_el(3));

VX=-(n*eq_el(1)*(eq_el(3)+sinL))/sqrt(1-eq_el(2)^2-eq_el(3)^2);
VY=(n*eq_el(1)*(eq_el(2)+cosL))/sqrt(1-eq_el(2)^2-eq_el(3)^2);
 
r=X*f+Y*g;
v=VX*f+VY*g;

end