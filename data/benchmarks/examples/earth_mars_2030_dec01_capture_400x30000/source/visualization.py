"""Plots saved trajectories without calling a solver or ephemeris service."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter,MaxNLocator
import numpy as np
from PIL import Image
from .data import AU_M, DAY_S, Trajectory,Scales

BODY_LABELS={'Earth':('Земля','Земли'),'Sun':('Солнце','Солнца'),'Moon':('Луна','Луны'),
             'Mercury':('Меркурий','Меркурия'),'Venus':('Венера','Венеры'),
             'Mars':('Марс','Марса'),'Jupiter':('Юпитер','Юпитера'),
             'Saturn':('Сатурн','Сатурна'),'Uranus':('Уран','Урана'),'Neptune':('Нептун','Нептуна'),
             'Apophis':('Апофис','Апофиса'),'Eros':('Эрос','Эроса'),'Bennu':('Бенну','Бенну'),
             'Ryugu':('Рюгу','Рюгу'),'Polyhymnia':('Полигимния','Полигимнии'),'Ceres':('Церера','Цереры'),
             'Vesta':('Веста','Весты')}


def _label(text):
    for english,(name,genitive) in BODY_LABELS.items():
        text=text.replace('Орбита '+english,'Орбита '+genitive).replace(english,name)
    return text


def _segments(ax, r, active):
    # Each sampled edge belongs to its left endpoint. No artificial gaps or
    # connection across separated active arcs; keep boundary points in both.
    for value, style, width in [(True, '-', 2.6), (False, '--', 2.0)]:
        starts = np.flatnonzero(np.r_[True, np.diff(active.astype(int)) != 0])
        for start, stop in zip(starts, np.r_[starts[1:], len(active)-1]):
            if active[start] == value and stop > start:
                ax.plot(r[start:stop+1, 0], r[start:stop+1, 1], style,
                        color='black', linewidth=width, zorder=3)


def preview_jpeg(source, target):
    with Image.open(source) as source_image:
        im = source_image.convert('RGB')
        im.thumbnail((1280, 1280))
        for quality in (88, 80, 70, 60):
            im.save(target, quality=quality, optimize=True)
            if Path(target).stat().st_size <= 200*1024:
                break
    with Image.open(target) as check:
        if check.format != 'JPEG' or max(check.size) > 1600 or Path(target).stat().st_size > 200*1024:
            raise ValueError('Preview exceeds JPEG context limits')


def _presentation(trajectory):
    meta=trajectory.metadata
    title=_label(meta.get('title',meta['case_id']))
    # The historical UMMP has a power-dependent engine, not constant F,c.
    if meta.get('status')=='imported_reference' or 'mission' not in meta:
        return title,''
    mission=meta['mission'];hardware=mission['spacecraft'];model=meta.get('bounded_model')
    final=False
    if model is not None:
        from .contract import audit_configuration
        if meta.get('stage')=='psi' and meta.get('status')=='verified_extremal' and meta.get('verification',{}).get('passed'):
            try:
                audit_configuration(trajectory,require_final=True)
                final=True
            except (ValueError,KeyError):
                pass
        kind='ПСИ' if final else 'промежуточная модель'
        title=_label(f"{mission['departure']} → {mission['target']}: {kind}, {mission['mass_kg']:g} кг")
    parameters=(f"F={hardware['thrust_N']*1000:g} мН; c={hardware['exhaust_velocity_m_s']/1000:g} км/с; "
                f"m₀={mission['mass_kg']:g} кг; mсух={hardware['dry_mass_kg']:g} кг")
    if not final:parameters='Задано: '+parameters
    if model is not None and not final:
        scales=Scales(**meta['scales'])
        force=model['a_max']*scales.acceleration_m_s2*mission['mass_kg']
        parameters+=f"\nМодель: F={force*1000:.6g} мН; α={model['alpha']:g}; β={model['beta']:g}"
    epoch=mission['launch_tdb'].replace('T',' ')
    duration=trajectory.arrays['t_s'][-1]/DAY_S
    if meta.get('stage')=='planet_capture':
        parameters+=f"\nПланетоцентрический участок; T={duration:.2f} сут"
    else:parameters+=f"\nСтарт {epoch} TDB; T={duration:g} сут"
    return title,parameters


def _headings(fig,ax,title,caption):
    if caption:
        fig.suptitle(title,fontweight='bold',fontsize=15)
        ax.set_title(caption,fontsize=9,pad=10)
    else:ax.set_title(title,fontweight='bold')


def render(trajectory: Trajectory, output):
    trajectory.validate()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    meta, a = trajectory.metadata, trajectory.arrays
    title,caption=_presentation(trajectory)
    if meta.get('stage')=='departure':
        quantity='Δv₀' if meta.get('departure_quantity')=='parking_orbit_delta_v' else 'v∞'
        title+=f"; {quantity} = {meta['departure']['norm_m_s']/1000:.2f} км/с"
    unit = AU_M if meta['center'] == 'Sun' else 1000.
    label = 'а.е.' if meta['center'] == 'Sun' else 'км'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 14})
    fig, ax = plt.subplots(figsize=(12, 7), layout='constrained')
    handles = []
    for overlay in meta.get('overlays', []):
        r = a[overlay['array']]/unit
        h, = ax.plot(r[:, 0], r[:, 1], overlay.get('linestyle', ':'),
                     color=overlay.get('color', '.8'), linewidth=1.3,
                     label=_label(overlay['label']), zorder=1)
        handles.append(h)
    names = {key:value[0] for key,value in BODY_LABELS.items()}
    center_color={'Sun':'#ff9900','Mars':'#df481d'}.get(meta['center'],'#3e80cc')
    handles.append(ax.scatter([0], [0], color=center_color, edgecolors='.3', s=65,
                              label=names.get(meta['center'], meta['center']), zorder=5))
    late_handles = []
    for marker in meta.get('markers', []):
        r = np.asarray(marker['r_m'])/unit
        color = marker.get('color', '#0052df')
        h = ax.scatter(r[0], r[1], s=80,
                                  facecolors='none' if marker.get('hollow') else color,
                                  edgecolors=color, linewidths=1.7,
                                  label=_label(marker['label']), zorder=5)
        (late_handles if marker.get('role') == 'target' else handles).append(h)
    r = a['r_m']/unit
    active = np.asarray(a.get('active', np.ones(len(r), dtype=bool)), dtype=bool)
    _segments(ax, r, active)
    if active.any():
        handles.append(Line2D([], [], color='k', linewidth=2.6, label='Активный участок'))
    if not active.all():
        handles.append(Line2D([], [], color='k', linestyle='--', linewidth=2, label='Пассивный участок'))
    handles.extend(late_handles)
    ax.set(xlabel=f'x, {label}', ylabel=f'y, {label}')
    if meta['center']!='Sun':
        ax.ticklabel_format(axis='both',style='sci',scilimits=(0,0),useMathText=True)
    _headings(fig,ax,title,caption)
    if 'plot_limits' in meta:
        ax.set_xlim(meta['plot_limits']['x'])
        ax.set_ylim(meta['plot_limits']['y'])
    ax.set_aspect('equal', adjustable='box')
    ax.grid(alpha=.22)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=11)
    fig.savefig(output/'trajectory.svg')
    fig.savefig(output/'trajectory.png', dpi=180)
    preview_jpeg(output/'trajectory.png', output/'trajectory_preview.jpg')
    plt.close(fig)
    fig = plt.figure(figsize=(10, 8), layout='constrained')
    ax = fig.add_subplot(111, projection='3d')
    if meta['center']!='Sun':
        for axis in (ax.xaxis,ax.yaxis,ax.zaxis):
            formatter=ScalarFormatter(useMathText=True)
            formatter.set_powerlimits((0,0))
            axis.set_major_formatter(formatter)
            axis.set_major_locator(MaxNLocator(nbins=5))
    points = [r]
    for overlay in meta.get('overlays', []):
        positions = a[overlay['array']]/unit
        points.append(positions)
        ax.plot(*positions.T, linestyle=overlay.get('linestyle', ':'),
                color=overlay.get('color', '.8'), linewidth=1, label=_label(overlay['label']))
    starts = np.flatnonzero(np.r_[True, np.diff(active.astype(int)) != 0])
    for start, stop in zip(starts, np.r_[starts[1:], len(active)-1]):
        if stop > start:
            ax.plot(*r[start:stop+1].T, color='k', linestyle='-' if active[start] else '--', linewidth=2)
    for marker in meta.get('markers', []):
        color=marker.get('color','#0052df')
        ax.scatter(*(np.asarray(marker['r_m'])/unit),facecolors='none' if marker.get('hollow') else color,
                   edgecolors=color,s=35,label=_label(marker['label']))
    ax.scatter(0,0,0,color=center_color,edgecolors='.3',s=45,label=names.get(meta['center'],meta['center']))
    bounds = np.vstack(points+[np.zeros((1, 3))])
    middle = (bounds.min(axis=0)+bounds.max(axis=0))/2
    radius = max(np.ptp(bounds, axis=0).max()/2, .01)
    ax.set(xlim=(middle[0]-radius, middle[0]+radius),
           ylim=(middle[1]-radius, middle[1]+radius),
           zlim=(middle[2]-radius, middle[2]+radius),
           xlabel=f'x, {label}', ylabel=f'y, {label}', zlabel=f'z, {label}')
    _headings(fig,ax,title,caption)
    ax.set_box_aspect((1, 1, 1))
    fig.savefig(output/'trajectory_3d.svg')
    fig.savefig(output/'trajectory_3d.png', dpi=150)
    preview_jpeg(output/'trajectory_3d.png', output/'trajectory_3d_preview.jpg')
    plt.close(fig)
    channels = [k for k in ('thrust_N', 'mass_kg') if k in a]
    if 'thrust_N' not in a and 'acceleration_m_s2' in a:channels.insert(0,'acceleration_m_s2')
    if 'switching_function' in a and meta.get('bounded_model',{}).get('alpha')==1:channels.append('switching_function')
    if channels:
        fig, axes = plt.subplots(len(channels), 1, figsize=(11, 3*len(channels)),
                                 sharex=True, squeeze=False, layout='constrained')
        if caption:_headings(fig,axes[0,0],title,caption)
        for ax, key in zip(axes[:, 0], channels):
            if key == 'thrust_N':
                ax.step(a['t_s']/DAY_S, a[key]*1000, where='post', color='k')
                ax.set_ylabel('Тяга, мН')
            elif key=='mass_kg':
                ax.plot(a['t_s']/DAY_S, a[key], color='k')
                ax.set_ylabel('Масса, кг')
            elif key=='acceleration_m_s2':
                ax.plot(a['t_s']/DAY_S,np.linalg.norm(a[key],axis=1)*1000,color='k')
                ax.set_ylabel('Ускорение, мм/с²')
            else:
                ax.plot(a['t_s']/DAY_S,a[key],color='k')
                ax.axhline(0,color='.6',linewidth=.8)
                ax.set_ylabel('Функция переключения')
            ax.grid(alpha=.22)
            if 'join_time_s' in meta:
                ax.axvline(meta['join_time_s']/DAY_S,color='#b04a28',linewidth=1,linestyle=':',label='Вход в сферу планеты')
        if 'join_time_s' in meta:axes[0,0].legend(fontsize=9)
        axes[-1, 0].set_xlabel('Время от входа в сферу, сут' if meta.get('stage')=='planet_capture' else 'Время от старта, сут')
        fig.savefig(output/'profiles.svg')
        fig.savefig(output/'profiles.png', dpi=160)
        preview_jpeg(output/'profiles.png', output/'profiles_preview.jpg')
        plt.close(fig)
    if meta.get('stage')=='planet_capture':_render_capture_orbit(trajectory,output)
    return output


def _render_capture_orbit(trajectory,output):
    """Orbit-plane overview and close-up, using saved states only."""
    a=trajectory.arrays;orbit=trajectory.metadata['orbit']
    r,v=a['r_m'][-1],a['v_m_s'][-1];mu=orbit['mu_m3_s2']
    normal=np.cross(r,v);normal/=np.linalg.norm(normal)
    evec=np.cross(v,np.cross(r,v))/mu-r/np.linalg.norm(r)
    ex=evec/np.linalg.norm(evec);ey=np.cross(normal,ex)
    xy=a['r_m']@np.column_stack([ex,ey])/1000.
    rp=(orbit['planet_radius_m']+orbit['periapsis_altitude_m'])/1000.
    ra=(orbit['planet_radius_m']+orbit['apoapsis_altitude_m'])/1000.
    semimajor=(rp+ra)/2;e=(ra-rp)/(ra+rp);u=np.linspace(0,2*np.pi,800)
    ellipse=semimajor*np.c_[np.cos(u)-e,np.sqrt(1-e*e)*np.sin(u)]
    fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained')
    for ax in axes:
        _segments(ax,xy,a['active'])
        for line in ax.lines:line.set_linewidth(.85)
        ax.plot(*ellipse.T,color='#c53c18',linewidth=1.3,label='Конечная орбита')
        ax.add_patch(plt.Circle((0,0),orbit['planet_radius_m']/1000,color='#df633b',label=_label(trajectory.metadata['center'])))
        ax.scatter(*xy[-1],s=30,color='#c53c18',zorder=5)
        ax.set_aspect('equal');ax.grid(alpha=.22);ax.set(xlabel='ξ, км',ylabel='η, км')
        ax.ticklabel_format(axis='both',style='sci',scilimits=(0,0),useMathText=True)
    axes[0].scatter(*xy[0],facecolors='none',edgecolors='#0052df',label='Вход в сферу')
    axes[0].set_title('Весь планетоцентрический участок')
    axes[0].legend(fontsize=9)
    axes[1].set(xlim=(-1.12*ra,1.5*rp),ylim=(-.65*ra,.65*ra),title='Скрутка и конечная орбита')
    fig.suptitle(f"{_label(trajectory.metadata['center'])}: скрутка на орбиту {orbit['periapsis_altitude_m']/1000:g} × {orbit['apoapsis_altitude_m']/1000:g} км\nВ плоскости орбиты; сплошная — тяга, штриховая — пассивный участок",fontsize=13)
    fig.savefig(output/'capture_orbit.svg');fig.savefig(output/'capture_orbit.png',dpi=180)
    preview_jpeg(output/'capture_orbit.png',output/'capture_orbit_preview.jpg');plt.close(fig)
