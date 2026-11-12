import unittest
from unittest.mock import patch
from dataclasses import replace
import numpy as np
from trajectory_pipeline.orbit_sources import OrbitSources,preset_elements,validate_sources
from trajectory_pipeline.ephemerides import Ephemerides
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.irt import _module
from trajectory_pipeline.contract import configuration_hash

class OrbitSourceTests(unittest.TestCase):
    def test_presets_against_legacy_orbital_conversion(self):
        tb=_module('_pipeline_iltt','ILTT/ILTTToolbox.py')
        for name in ('Apophis','ApophisNew'):
            el=preset_elements(name);provider=OrbitSources({'apophis':dict(kind='kepler',preset=name)})
            for jd in (2461800.5,el['epoch_jd'],2462600.5):
                n=np.sqrt(el['mu_m3_s2']/el['a_m']**3)
                M=np.deg2rad(el['M_deg'])+(jd-el['epoch_jd'])*86400*n
                E=tb.EAnomaly(el['e'],M);nu=2*np.arctan2(np.sqrt(1+el['e'])*np.sin(E/2),np.sqrt(1-el['e'])*np.cos(E/2))
                r,v=tb.orb2rv(el['a_m']*(1-el['e']**2),el['e'],*np.deg2rad([el['i_deg'],el['node_deg'],el['peri_deg']]),nu,el['mu_m3_s2'])
                np.testing.assert_allclose(provider.state('Apophis',jd),np.r_[r[0],v[0]],rtol=1e-12,atol=.001)

    def test_kepler_early_path_does_not_read_ephemerides(self):
        m=Mission.load('configs/apophis_new_early.json')
        from trajectory_pipeline.iltt_entry import angular_branches
        # Sun's zero state requires no backend data either.
        with patch.object(Ephemerides,'_table',side_effect=AssertionError('table read')):
            angular_branches(m)
            a,b,_=replace(m,tof_days=350).boundary()
            self.assertTrue(np.isfinite(np.r_[a,b]).all())

    def test_selection_is_explicit_and_changes_contract(self):
        m=Mission.load('configs/apophis_new_early.json');a=replace(m,tof_days=350)
        b=replace(a,orbit_sources={'apophis':{'kind':'kepler','preset':'Apophis'}})
        self.assertNotEqual(configuration_hash(a),configuration_hash(b))
        post=a.ephemerides().state('apophis',2461800.5)
        pre=b.ephemerides().state('apophis',2461800.5)
        self.assertGreater(np.linalg.norm(post[:3]-pre[:3]),1e9)
        self.assertNotIn('orbit_sources',replace(a,orbit_sources=None).to_dict())

    def test_invalid_source_is_not_ignored(self):
        for spec in ({'apophis':{'kind':'typo'}},{'earth':{'kind':'kepler','preset':'ApophisNew'}},{'Apophis':{'kind':'ephemerides'},'apophis':{'kind':'ephemerides'}}):
            with self.assertRaises(ValueError):validate_sources(spec)

    def test_vector_scalar_and_velocity(self):
        p=OrbitSources({'apophis':{'kind':'kepler','preset':'ApophisNew'}});jd=2461800.5
        array=p.state('apophis',[jd,jd+1,jd+2])
        np.testing.assert_array_equal(array[0],p.state('apophis',jd))
        dt=.001
        v=(p.state('apophis',jd+dt)[:3]-p.state('apophis',jd-dt)[:3])/(2*dt*86400)
        np.testing.assert_allclose(v,array[0,3:],rtol=3e-7,atol=.001)
        np.testing.assert_array_equal(p.state('apophis',jd,'apophis'),np.zeros(6))


    def test_real_transition_and_relabel_rejection(self):
        import tempfile
        from pathlib import Path
        from copy import deepcopy
        from trajectory_pipeline.irt import solve_irt
        from trajectory_pipeline.orbit_transition import reconcile_irt
        from trajectory_pipeline.verification import verify_irt
        from trajectory_pipeline.contract import audit_configuration,make_request
        mission=Mission.load('configs/apophis_new_early.json')
        source,diag=solve_irt(mission)
        self.assertIsNotNone(source,diag)
        full={'earth':{'kind':'ephemerides'},'apophis':{'kind':'ephemerides'}}
        with tempfile.TemporaryDirectory(dir='runs') as folder:
            result,summary=reconcile_irt(source,full,Path(folder)/'full')
            self.assertEqual(summary['status'],'completed_stage')
            self.assertTrue(verify_irt(result)['passed'])
            self.assertEqual(result.metadata['orbit_source_transition']['status'],'completed_stage')
            self.assertEqual(result.metadata['mission']['mass_kg'],204)
            self.assertNotIn('mass_kg',result.arrays)
            self.assertEqual(result.metadata['mission']['tof_days'],source.metadata['mission']['tof_days'])
            wrong=deepcopy(source)
            wrong.metadata['mission']['orbit_sources']=full
            m=Mission(**wrong.metadata['mission'])
            with self.assertRaises(ValueError):audit_configuration(wrong,m,make_request(m))
