function JD = calc_JD(t)

% This function transforms the calendar date structure t to Julian date
% ---------------------------------------------------------------------
a=floor((14-t.month)/12);
y=t.year+4800-a;
m=t.month+12*a-3;
JD=t.day+floor((153*m+2)/5)+365*y+floor(y/4)-floor(y/100)+floor(y/400)-32045+(t.hour-12)/24+t.minute/1440+t.second/86400;

end