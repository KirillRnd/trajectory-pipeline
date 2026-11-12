import numpy as np
from trajectory_pipeline.data import Trajectory,Scales,write_json
from trajectory_pipeline.bangbang import _sampling_times
src=Trajectory.load('runs/apophis_daily_routes_v1/chains/2028-02-25/physical')
scale=Scales(**src.metadata['scales']).time_s
old=src.arrays['t_s']/scale
for factor in np.linspace(.5,1.5,1001):
    tf=old[-1]*factor
    edges=np.r_[0,np.asarray(src.metadata['switch_times_s'])/scale*factor,tf]
    times=_sampling_times(old*tf/old[-1],edges,scale)
    uncovered=~np.any([(times>=a)&(times<=b) for a,b in zip(edges[:-1],edges[1:])],axis=0)
    if uncovered.any():
        info=dict(factor=float(factor),end=tf,last_time=float(times[-1]),overshoot_s=float((times[-1]-tf)*scale),uncovered=int(uncovered.sum()))
        print(info);write_json('runs/apophis_daily_routes_v1/clock_regression.json',info);break
else:print('No uncovered samples')
