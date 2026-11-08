#Скорость С1

import numpy as np

sin = np.sin
cos = np.cos
log = np.log
sqrt = np.sqrt

mu = 3.0393890e-6


def v2_C1(x0):
    x =  (np.sqrt((1-mu)/(x0 + mu)) - (x0 + mu)) + (0.47084948*x0 + (x0 - 0.21319899)*(1.1044086*x0/np.cos(0.24954179 - 2.0628507/np.log(x0)) - 0.0420995)*(np.sin(2.117359/np.log(x0)) + 0.014023513)/(x0 - 0.92994696))*1e-5
    return x

#Период С1
_T_RES1 = 0.6299598867   # резонанс 2:1
_T_RES3 = 0.8254809759   # резонанс 4:3
_T_RES5 = 0.8855479105   # резонанс 5:4



def T_C1(x_in):
    scalar = np.ndim(x_in) == 0
    x0 = np.atleast_1d(np.asarray(x_in, float))
    result = np.empty_like(x0)

    m_inner   = (x0 >= _T_RES1) & (x0 <= _T_RES3)
    m_inner_1 = (x0 >  _T_RES3)
    m_outer   = ~(m_inner | m_inner_1)

    if m_inner.any():
        x0i  = x0[m_inner]
        T_an = 2 * np.pi * (x0i + mu) / (np.sqrt((1 - mu) / (x0i + mu)) - (x0i + mu))
        dT   = (
            0.0708184812274564
            * (sin(T_an * sin(x0i)) - (-0.5684899)) ** 2
            * cos(np.cos(2 * np.pi * T_an) + 0.43404695) ** 2
            + (0.24887557 * abs(np.sin(2 * np.pi * T_an) / (T_an * sin(T_an * (-0.23598689)))))
            / (-0.46599796)
            - (-0.0305596)
        ) * cos(T_an) ** 3
        result[m_inner] = T_an + dT

    if m_inner_1.any():
        x0i = x0[m_inner_1]
        _T_an = 2 * np.pi * (x0i + mu) / (np.sqrt((1 - mu) / (x0i + mu)) - (x0i + mu))
        dT = (cos(_T_an*(-1.0967953)) - 1*0.40994662)**3*sin(_T_an)*cos(sin(2.73365805536006*_T_an**3 + 0.102532)/cos(sin(_T_an)))*cos(1.1085341 - np.cos(2 * np.pi * _T_an)/(-0.00036840152))**2

        result[m_inner_1] = _T_an + dT


    if m_outer.any():
        x0o = x0[m_outer]
        result[m_outer] = (
            2 * np.pi * (x0o + mu) / (np.sqrt((1 - mu) / (x0o + mu)) - (x0o + mu))
            + (x0o ** 14.47737
               * (x0o - 0.7659898)
               * (654.6419 * sin(289.54312 / x0o) + 246.73122)
               * (sin(6.09837867894604 * x0o / (x0o - 1.0300114)) - 0.31069863)
               * cos(718.70135 * x0o)
               / sin(289.54312 / x0o)) * 1e-2
        )

    return float(result[0]) if scalar else result
#скорость С2

_XR_12 = 1.5874010519681994
_XR_23 = 1.3103706971044482
_XR_34 = 1.2114137285547597
_XR_45 = 1.1603972084031948
_XR_56 = 1.129243234657234


def v2_C2(x_in):
    scalar = np.ndim(x_in) == 0
    x0 = np.atleast_1d(np.asarray(x_in, float))
    result = np.full_like(x0, np.nan)

    m1  =  x0 <  _XR_34
    m2a = (x0 >= _XR_34) & (x0 <  _XR_23)
    m2b = (x0 >= _XR_23) & (x0 <  _XR_12)
    m3  =  x0 >= _XR_12

    if m1.any():
        x0i = x0[m1]
        result[m1] = (
            (1.0/np.sqrt(x0i) - x0i)
            + sin((1.0/(x0i - 1.1292432347) - 0.10267362)/0.03677166)**2
            / (1.0/(x0i - 1.2114137286)
                + (1.0/(x0i - 1.1603972084)*(-0.3521499)
                    - 1.0/(x0i - 1.1292432347))*0.76316553)**2
        )
    if m2a.any():
        x0i = x0[m2a]
        result[m2a] = (
            (1.0/np.sqrt(x0i) - x0i)
            + (1.270627*(
                0.0068164775*1.0/(x0i - 1.3103706971)
                *(cos(1.0/(x0i - 1.3103706971) + 1.1860751) - 1.2091384)
                - log(0.95528644/(
                    sqrt(1.0/(x0i - 1.2114137286))
                    + 0.10899513/cos(1.0/(x0i - 1.3103706971)**2 - 1.219088)
                ))/(0.723822227234289*1.0/(x0i - 1.3103706971)
                    + cos(1.0/(x0i - 1.3103706971)**2))
            )**3) / 100
        )
    if m2b.any():
        x0i = x0[m2b]
        result[m2b] = (
            (1.0/np.sqrt(x0i) - x0i)
            + ((1.0/(x0i - 1.5874010520)
                - 1.0/(x0i - 1.5874010520)
                /(-1.0/(x0i - 1.3103706971)**2/(-0.081530765)
                    + 1.0/(x0i - 1.5874010520)))
                *(-(-4.0431805e-5
                    - 0.0007244709*x0i
                    /(1.0/(x0i - 1.3103706971)**2*1.0/(x0i - 1.5874010520)))
                    *(1.0/(x0i - 1.3103706971)
                    + (-(-0.7619614)*1.0/(x0i - 1.3103706971)**2
                        + 1.0/(x0i - 1.5874010520))*(-0.00037295598))
                    - 0.00018975961)/x0i) / 100
        )
    if m3.any():
        x0i = x0[m3]
        result[m3] = (
            (1.0/np.sqrt(x0i) - x0i)
            + sin(x0i)**3*3.1719075e-5/(1.5869833 - x0i) / 100
        )

    return float(result[0]) if scalar else result


#период C2

_XT_RES12 = 1.5874010519681994
_XT_RES23 = 1.3103706971044482
_XT_RES34 = 1.2114137285547597

def T_C2(x_in):
    scalar = np.ndim(x_in) == 0
    x0 = np.atleast_1d(np.asarray(x_in, float))
    result = np.empty_like(x0)

    m1  =  x0 <  _XT_RES34
    m2a = (x0 >= _XT_RES34) & (x0 <  _XT_RES23)
    m2b = (x0 >= _XT_RES23) & (x0 <  _XT_RES12)
    m3  =  x0 >= _XT_RES12

    if m1.any():
        xi  = x0[m1]
        T_a = 2*np.pi / (xi**(-1.5) - 1)
        x5  = 1.0 / (xi - 1.1603972084)
        x6  = 1.0 / (xi - 1.1292432347)
        result[m1] = T_a + (
            (sin(x6 + 1.1336251)*cos(T_a + x5)*cos(x5 - 1.4154433)/(-0.6173846)
             + cos(-1.9481502/xi))**2
            - 0.0885539
            + 0.014037436/sin(-x6 - 1.1778307)
        )
    if m2a.any():
        xi  = x0[m2a]
        T_a = 2*np.pi / (xi**(-1.5) - 1)
        s_T = np.sin(T_a)
        c_T = np.cos(T_a)
        d23 = xi - 1.3103706971
        x5  = 1.0 / d23
        x6  = 1.0 / d23**2
        x7  = 1.0 / (xi - 1.2114137286)
        result[m2a] = T_a + (
            (-0.34854093*(-xi + s_T**2)/(x5 + 0.0039276746*x6)
             + 3.14628173937857*(0.682444697070306*c_T
                                 + 0.682444697070306*sin(19.8649828762854*d23 + x5)
                                 + 1)**3 / x7**1.5)
            * (sin(c_T) + 0.60880077)
        )
    if m2b.any():
        xi  = x0[m2b]
        T_a = 2*np.pi / (xi**(-1.5) - 1)
        s_T = np.sin(T_a)
        c_T = np.cos(T_a)
        d23 = xi - 1.3103706971
        x5  = 1.0 / d23
        x6  = 1.0 / d23**2
        x7  = 1.0 / (xi - 1.5874010520)
        result[m2b] = T_a + (
            (-c_T + x5)
            * (-(-4.455732e-6)
               * (-T_a * (-x7 + 32644.3662333504
                          * (0.00553472285871535*c_T + 1.0/(x6 + 0.5307582/s_T))**2)
                  * (s_T*4.97912 + c_T)
                  + x5)
               - 0.014976744)
            + 0.14733754
        ) / 100
    if m3.any():
        xi  = x0[m3]
        T_a = 2*np.pi / (xi**(-1.5) - 1)
        s_T = np.sin(T_a)
        c_T = np.cos(T_a)
        result[m3] = T_a + (
            T_a * (c_T + 1.0282876)
            * (7.78293717143056e-8
               * (xi/0.5005733 + T_a + sin(s_T*2.1873882) + 0.26198676)**2)
            / s_T
        )

    return float(result[0]) if scalar else result


# Backward-compatible names used in old notebooks.
v2 = v2_C2
T_2 = T_C2
