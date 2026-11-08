function [p,ex,ey,ix,iy,L] = orb2equintoctial(p,e,i,O,o,nu)
%Кеплеровы элементы в равноденственные
ex = e*cos(o+O);
ey = e*sin(o+O);
ix = tan(i/2)*cos(O);
iy = tan(i/2)*sin(O);
L = O+o+nu;
end