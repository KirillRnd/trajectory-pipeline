"""Historical UMMP propulsion and its constant-exhaust fuel homotopy."""
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from .data import AU_M, DAY_S, Scales


@dataclass(frozen=True)
class UmmpEngine:
    power_at_au_W: float = 713.
    reserve_W: float = 60.
    degradation_per_year: float = .1
    year_s: float = 365.256363004 * DAY_S
    mass_compensation: float = 1.3
    power_exponent: float = 1.7
    minimum_power_W: float = 200.
    maximum_power_W: float = 450.

    def performance(self, time_s, radius_m):
        """Available power, force, exhaust, flow, and radial derivatives in SI."""
        sunlight = np.maximum(1-self.degradation_per_year*time_s/self.year_s, 0)
        raw_power = sunlight*self.power_at_au_W*(radius_m/AU_M)**-self.power_exponent-self.reserve_W
        power = np.minimum(raw_power, self.maximum_power_W)
        available = power >= self.minimum_power_W
        dp = np.where(available & (raw_power < self.maximum_power_W),
                      -self.power_exponent*(raw_power+self.reserve_W)/radius_m, 0.)
        thrust = np.where(available, 1e-3*(.0527*power+1.5667), 0.)
        exhaust = np.where(available, 9.80665*(-.0006*power**2+1.0584*power+999.2504), 0.)
        safe_exhaust = np.where(available, exhaust, 1.)
        flow = self.mass_compensation*thrust/safe_exhaust
        dthrust = .0000527*dp
        dexhaust = 9.80665*(1.0584-.0012*power)*dp
        dflow = self.mass_compensation*(dthrust-thrust*dexhaust/safe_exhaust)/safe_exhaust
        return power, thrust, exhaust, flow, dthrust, dflow


@dataclass(frozen=True)
class UmmpModel:
    scales: Scales
    mass_kg: float
    baseline_thrust_N: float
    baseline_exhaust_m_s: float
    fraction: float
    engine: UmmpEngine = UmmpEngine()

    alpha: ClassVar[float] = 1.
    variable_mass: ClassVar[bool] = True
    gravity: ClassVar[None] = None
    dimension: ClassVar[int] = 14
    pv_slice: ClassVar[slice] = slice(10, 13)

    @property
    def a_max(self):
        return self.baseline_thrust_N/(self.mass_kg*self.scales.acceleration_m_s2)

    @property
    def fuel_weight(self):
        return self.baseline_exhaust_m_s/self.scales.velocity_m_s

    def coefficients(self, t, radius):
        _, force, _, flow, dforce, dflow = self.engine.performance(
            t*self.scales.time_s, radius*self.scales.distance_m)
        s = self.fraction
        force_unit = self.mass_kg*self.scales.acceleration_m_s2
        flow_unit = self.mass_kg/self.scales.time_s
        baseline_flow = self.baseline_thrust_N/self.baseline_exhaust_m_s
        return (((1-s)*self.baseline_thrust_N+s*force)/force_unit,
                ((1-s)*baseline_flow+s*flow)/flow_unit,
                s*dforce*self.scales.distance_m/force_unit,
                s*dflow*self.scales.distance_m/flow_unit)

    def switching(self, y, t):
        force, flow, _, _ = self.coefficients(t, np.linalg.norm(y[:3], axis=0))
        return force*np.linalg.norm(y[10:13], axis=0)/y[6]-flow*(y[13]+self.fuel_weight)

    def rhs(self, t, y, throttle):
        r,v,m,pr,pv,pm = y[:3],y[3:6],y[6],y[7:10],y[10:13],y[13]
        radius = np.linalg.norm(r)
        if m <= 0 or radius < 1e-6:
            raise ValueError('Nonpositive mass or central collision during UMMP propagation')
        force, flow, df, dq = self.coefficients(t, radius)
        primer = np.linalg.norm(pv)
        acceleration = throttle*force/m*pv/max(primer, 1e-15)
        engine_gradient = throttle*(df*primer/m-dq*(pm+self.fuel_weight))*r/radius
        pr_dot = pv/radius**3-3*r*np.dot(r,pv)/radius**5-engine_gradient
        return np.r_[v, -r/radius**3+acceleration, -throttle*flow,
                     pr_dot, -pr, throttle*force*primer/m**2]
