"""Read-only figures for saved four-mode missions, including impulse jumps."""
from pathlib import Path
import json
import numpy as np
from scipy.interpolate import CubicHermiteSpline
from .data import Trajectory,DAY_S,AU_M,sha256
from .visualization import preview_jpeg,plt,_segments,_label


def _local_curve(arrays):
    """Hermite display interpolation uses stored velocities; no propagation."""
    r=arrays['r_m'];t=arrays['t_s']
    angles=np.arctan2(np.linalg.norm(np.cross(r[:-1],r[1:]),axis=1),np.sum(r[:-1]*r[1:],axis=1))
    counts=np.maximum(1,np.ceil(angles/.08).astype(int))
    points=np.r_[np.concatenate([np.linspace(left,right,int(n)+1)[:-1] for left,right,n in zip(t[:-1],t[1:],counts)]),t[-1]]
    return CubicHermiteSpline(t,r,arrays['v_m_s'])(points)


def render_orbital_mission(folder,output):
    p=Path(folder);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if (p/'capture_search.json').exists():
        from .capture_search import verify_capture_search
        check=verify_capture_search(p)
        if not check['passed']:raise ValueError('Cannot render an unverified capture search selection')
        return render_orbital_mission(p/check['selected_folder'],output)
    dep,arr,whole=[Trajectory.load(p/name) for name in ('departure','arrival','final')]
    if whole.metadata['impulses_sha256']!=sha256(p/'impulses.json'):raise ValueError('Impulse event checksum differs from the plotted mission')
    m=whole.metadata['mission'];modes=m['orbital_maneuvers'];events=json.loads((p/'impulses.json').read_text())
    names={'spiral':'малая тяга','impulse':'импульс'}
    title=_label(f"Земля → {m['target']}: {names[modes['departure']['kind']]} / {names[modes['arrival']['kind']]}")
    fig,ax=plt.subplots(figsize=(11,7),layout='constrained')
    outer=Trajectory.load(p/'outer')
    for overlay in outer.metadata.get('overlays',[]):
        r=outer.arrays[overlay['array']]/AU_M
        ax.plot(r[:,0],r[:,1],linestyle=overlay.get('linestyle',':'),color=overlay.get('color','.8'),linewidth=1,label=_label(overlay['label']))
    _segments(ax,whole.arrays['r_m']/AU_M,whole.arrays['active'])
    ax.scatter(0,0,color='#ff9900',s=45,label='Солнце')
    for index,name,color in [(0,'Исходная орбита','#1263bf'),(-1,'Конечная орбита','#d13c20')]:
        r=whole.arrays['r_m'][index]/AU_M;ax.scatter(*r[:2],color=color,s=40,label=name,zorder=5)
    ax.set_aspect('equal');ax.grid(alpha=.2);ax.set(xlabel='x, а.е.',ylabel='y, а.е.',title=title)
    ax.legend(fontsize=9,loc='upper left',bbox_to_anchor=(1.01,1))
    fig.savefig(output/'trajectory.svg');fig.savefig(output/'trajectory.png',dpi=170)
    preview_jpeg(output/'trajectory.png',output/'trajectory_preview.jpg');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained')
    for ax,traj,side,body in zip(axes,[dep,arr],['departure','arrival'],['Земля',m['target']]):
        a=traj.arrays;spec=modes[side]
        r=a['r_m'][0];h=np.cross(r,a['v_m_s'][0]);h/=np.linalg.norm(h);ex=r/np.linalg.norm(r);ey=np.cross(h,ex)
        xy=_local_curve(a)@np.column_stack([ex,ey])/1000.
        if spec['kind']=='spiral' and 'arcs' in traj.metadata['maneuver']:
            # Interpolate each actual arc separately; never infer active arcs
            # from a different angle function during plotting.
            spline=CubicHermiteSpline(a['t_s'],a['r_m'],a['v_m_s'])
            projection=np.column_stack([ex,ey])/1000.
            labelled=set()
            for arc in traj.metadata['maneuver']['arcs']:
                ts=np.unique(np.r_[arc['start_s'],a['t_s'][(a['t_s']>arc['start_s'])&(a['t_s']<arc['end_s'])],arc['end_s']])
                coords=spline(ts)@projection;on=arc['active']
                ax.plot(*coords.T,color='k',linestyle='-',linewidth=.6 if on else .12,
                        label=('Тяга включена' if on else 'Тяга выключена') if on not in labelled else None)
                labelled.add(on)
        elif spec['kind']=='spiral':ax.plot(*xy.T,color='k',linewidth=.5,label='Участок на малой тяге')
        else:ax.plot(*xy.T,'k--',linewidth=1.5,label='Пассивная дуга')
        ax.add_patch(plt.Circle((0,0),spec['planet_radius_m']/1000.,color='#4589cc' if side=='departure' else '#d95a32',label=_label(body)))
        ax.scatter(*xy[0],s=35,facecolors='none',edgecolors='#1263bf',label='Начало')
        ax.scatter(*xy[-1],s=30,color='#d13c20',label='Конец')
        ax.set_aspect('equal');ax.grid(alpha=.2);ax.set(xlabel='ξ, км',ylabel='η, км',title='Отлёт' if side=='departure' else 'Прибытие')
        ax.ticklabel_format(axis='both',style='sci',scilimits=(0,0),useMathText=True);ax.legend(fontsize=9)
    fig.suptitle(title,fontsize=14)
    fig.savefig(output/'local_maneuvers.svg');fig.savefig(output/'local_maneuvers.png',dpi=170)
    preview_jpeg(output/'local_maneuvers.png',output/'local_maneuvers_preview.jpg');plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True,layout='constrained')
    a=whole.arrays;t=a['t_s']/DAY_S;mass=a['mass_kg'].copy()
    arrival_event=next((e for e in events if e['kind']=='arrival_impulse'),None)
    if arrival_event:
        mass[-1]=arrival_event['mass_before_kg']
        t_mass=np.r_[t,t[-1]];mass=np.r_[mass,arrival_event['mass_after_kg']]
    else:t_mass=t
    axes[0].step(t,a['thrust_N']*1000,where='post',color='k');axes[0].set_ylabel('Тяга ЭРДУ, мН')
    axes[1].plot(t_mass,mass,color='k');axes[1].axhline(m['spacecraft']['dry_mass_kg'],color='.6',linestyle=':',label='Сухая масса')
    for ax in axes:
        ax.axvline(dep.arrays['t_s'][-1]/DAY_S,color='#aa5428',linestyle=':',label='Сфера Земли')
        ax.axvline(dep.arrays['t_s'][-1]/DAY_S+m['tof_days'],color='#7744aa',linestyle=':',label='Сфера цели')
        ax.grid(alpha=.2)
    for event in events:
        if event['kind']=='arrival_impulse':axes[1].annotate(f"Захват Δv={event['delta_v_m_s']:.1f} м/с",xy=(t[-1],event['mass_after_kg']),xytext=(-180,30),textcoords='offset points',arrowprops=dict(arrowstyle='->'),fontsize=10)
        else:axes[0].text(.015,.92,f"РБ: Δv={event['delta_v_m_s']/1000:.3f} км/с, мгновенно",transform=axes[0].transAxes,fontsize=10)
    axes[0].legend(fontsize=9);axes[1].set(xlabel='Время от исходной орбиты, сут',ylabel='Масса КА, кг')
    fig.suptitle(title+f"\nМасса на исходной орбите {m['mass_kg']:g} кг; топливо внешнего РБ не включено",fontsize=13)
    fig.savefig(output/'profiles.svg');fig.savefig(output/'profiles.png',dpi=170)
    preview_jpeg(output/'profiles.png',output/'profiles_preview.jpg');plt.close(fig)
    return output
