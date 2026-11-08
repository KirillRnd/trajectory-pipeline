"""Cross-check final PSI equations and control against unmodified KIAM Fortran."""
from importlib.metadata import version
import numpy as np
from .data import Scales
from .bounded_model import BoundedModel
from .bounded import canonical
from .ephemerides import _KIAM_LOCK


def verify_kiam_gravity(trajectory):
    """Compare the complete lunar gravity field with KIAM's N-body Fortran.

    KIAM evaluates native JPLEPH directly; the solver uses a frozen Hermite
    table. Sample between table knots to include interpolation error.
    """
    from kiam_astro import kiam
    from .gravity import Gravity
    spec=trajectory.metadata.get('gravity_spec')
    if spec is None:return dict(passed=True,applicable=False)
    gravity=Gravity(spec)
    if gravity.scale!=1:raise ValueError('Full N-body check requires complete lunar gravity')
    scales=Scales(**trajectory.metadata['scales'])
    eps=np.deg2rad(84381.448/3600.)
    rotation=np.array([[1,0,0],[0,np.cos(eps),np.sin(eps)],[0,-np.sin(eps),np.cos(eps)]])
    sources=kiam.prepare_sources_dict();sources.update(sun=True,moon=True)
    data=kiam.prepare_data_dict();data['jd_zero']=trajectory.metadata['epoch_jd']
    units=kiam.prepare_units_dict('earth')
    units.update(DistUnit=scales.distance_m/1000,VelUnit=scales.velocity_m_s/1000,
                 TimeUnit=scales.time_s/86400,AccUnit=scales.acceleration_m_s2,
                 EarthGM=1.,SunGM=spec['sun_mu_ratio'],MoonGM=spec['moon_mu_ratio'])
    indices=np.unique(np.linspace(0,len(trajectory.arrays['t_s'])-1,31,dtype=int))
    errors=[]
    with _KIAM_LOCK:
        for i in indices:
            time=float(trajectory.arrays['t_s'][i]/scales.time_s)
            r=trajectory.arrays['r_m'][i]/scales.distance_m
            actual=kiam.nbp_rv_earth(time,np.r_[rotation.T@r,np.zeros(3)],False,sources,data,units)
            expected,_=gravity.independent_scalar(time,r)
            errors.append(float(np.linalg.norm(rotation@actual[3:]-expected))*scales.acceleration_m_s2)
    maximum=max(errors)
    return dict(passed=bool(maximum<1e-8),applicable=True,samples=len(indices),
                maximum_acceleration_error_m_s2=maximum,tolerance_m_s2=1e-8,
                source='Unmodified KIAM nbp_rv_earth Fortran, native JPLEPH',package_version=version('kiam-astro'),
                scope='Earth + direct/indirect Moon and Sun point masses; matched gravitational constants; includes local table interpolation error')


def verify_kiam_psi(trajectory):
    from kiam_astro import optimal
    model=BoundedModel(**trajectory.metadata['bounded_model'])
    if not (model.variable_mass and model.beta==1 and model.alpha==1):
        raise ValueError('KIAM mass-optimal cross-check requires the final exact PSI model')
    scales=Scales(**trajectory.metadata['scales'])
    vex=trajectory.metadata['mission']['spacecraft']['exhaust_velocity_m_s']/scales.velocity_m_s
    y=canonical(trajectory,model)
    indices=np.unique(np.linspace(1,y.shape[1]-2,min(101,y.shape[1]-2),dtype=int))
    indices=[i for i in indices if np.linalg.norm(y[10:13,i])>1e-10 and abs(model.switching(y[:,i]))>1e-8]
    if not indices:raise ValueError('No interior points away from switches for an independent KIAM check')
    mapped=y[:,indices].copy()
    # Our Lagrange fuel functional is vex times expended mass fraction.
    # KIAM uses a Mayer terminal mass functional with p_m(tf)=1.
    mapped[7:13]/=vex
    mapped[13]=1+mapped[13]/vex
    errors=[]
    gravity_errors=[]
    central=BoundedModel(model.a_max,alpha=model.alpha,beta=model.beta,q=model.q,variable_mass=True)
    with _KIAM_LOCK:
        for column,index in enumerate(indices):
            actual=optimal.r2bp_pontr_mopt_bnd_f_rv(0.,mapped[:,column],False,model.a_max,vex,0.,1.)
            time=float(trajectory.arrays['t_s'][index]/scales.time_s)
            expected=central.rhs(time,y[:,index])
            if model.gravity is not None:
                total=model.rhs(time,y[:,index])
                r=y[:3,index];pv0=y[10:13,index];radius=np.linalg.norm(r)
                g,jac=model.gravity.independent_scalar(time,r)
                central_jac=(3*np.outer(r,r)/radius**2-np.eye(3))/radius**3
                difference=np.zeros(14);difference[3:6]=g+r/radius**3
                difference[7:10]=-(jac-central_jac)@pv0
                gravity_errors.append(float(np.max(np.abs(total-expected-difference))))
            expected[7:14]/=vex
            errors.append(float(np.max(np.abs(actual-expected))))
        magnitude,force=optimal.control_r2bp_pontr_mass_bnd_f_rv(mapped,model.a_max,vex,0.)
    pv=y[10:13,indices]
    control=model.a_max*model.throttle(y[:,indices])*pv/np.linalg.norm(pv,axis=0)
    force_error=float(np.max(np.abs(force-control)))
    maximum=max(errors)
    gravity_error=max(gravity_errors,default=0.)
    nbody=verify_kiam_gravity(trajectory)
    return dict(passed=bool(maximum<1e-9 and force_error<1e-10 and gravity_error<1e-9 and nbody['passed']),
                source='Unmodified KIAM Astro compiled Fortran equations and published control API',
                package_version=version('kiam-astro'),samples=len(indices),
                maximum_dimensionless_rhs_error=maximum,maximum_dimensionless_force_error=force_error,
                maximum_third_body_decomposition_error=gravity_error,
                nbody_gravity=nbody,
                costate_map='p_r,v(KIAM)=p_r,v/vex; p_m(KIAM)=1+p_m/vex; normalized initial mass=1',
                scope='KIAM central mass-optimal equations/control, plus independent third-body decomposition when present; not a separate global optimization')
