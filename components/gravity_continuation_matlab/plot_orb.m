function [] = plot_orb(eq_el,mu)

% This function plots the projection of the body's orbit onto the main plane using the equinoctial elements given
% ---------------------------------------------------------------------------------------------------------------
N=100;
r=zeros(3,N+1);

for i=1:N+1
    eq_el(6)=eq_el(6)+2*pi/N;
    r_temp=eq2cart(eq_el,mu);
    r(1:3,i)=r_temp;
end

plot(r(1,:),r(2,:),'-.k')