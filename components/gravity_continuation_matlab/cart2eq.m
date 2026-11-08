function eq_el = cart2eq(r,v,mu)

% This function transforms the Cartesian position and velocity to the equinoctial elements 
% ----------------------------------------------------------------------------------------
nr=norm(r);
nv=norm(v);

eq_el(1)=1/(2/nr-nv^2/mu);

w=cross(r,v)/norm(cross(r,v));

eq_el(4)=-w(2)/(1+w(3));
eq_el(5)=w(1)/(1+w(3));

f=[1+eq_el(4)^2-eq_el(5)^2; 2*eq_el(4)*eq_el(5); -2*eq_el(5)]/(1+eq_el(4)^2+eq_el(5)^2);
g=[2*eq_el(4)*eq_el(5); 1-eq_el(4)^2+eq_el(5)^2; 2*eq_el(4)]/(1+eq_el(4)^2+eq_el(5)^2);

e=-r/nr+cross(v,cross(r,v))/mu;

eq_el(2)=dot(e,f);
eq_el(3)=dot(e,g);

X=dot(r,f);
Y=dot(r,g);

b=1/(1+sqrt(1-eq_el(2)^2-eq_el(3)^2));

cosF=eq_el(2)+((1-eq_el(2)^2*b)*X-eq_el(2)*eq_el(3)*b*Y)/(eq_el(1)*sqrt(1-eq_el(2)^2-eq_el(3)^2));
sinF=eq_el(3)+((1-eq_el(3)^2*b)*Y-eq_el(2)*eq_el(3)*b*X)/(eq_el(1)*sqrt(1-eq_el(2)^2-eq_el(3)^2));

F=acos(cosF);

if sinF*sin(F)<0
    F=-F;
end

eq_el(6)=F-eq_el(2)*sinF+eq_el(3)*cosF;

end