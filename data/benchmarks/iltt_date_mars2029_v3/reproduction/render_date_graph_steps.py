"""Render saved date-first graph stages; no optimization or new search."""
from pathlib import Path
import json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from trajectory_pipeline.data import Trajectory,Scales,AU_M,DAY_S,sha256
from trajectory_pipeline.irt import _module
from trajectory_pipeline.ephemerides import Ephemerides
from trajectory_pipeline.visualization import preview_jpeg,_segments
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
g=json.loads((root/'graph.json').read_text())['nodes']
nid=next(k for k,n in g.items() if n['request']['operation']=='cold' and n['request']['mission']['solver']['iltt_branch']==0)
run=root/'nodes'/nid/'run';irt=Trajectory.load(run/'stage_irt'/'irt');rec=irt.metadata['mission']['solver']['iltt_resolved'];sc=Scales(**irt.metadata['scales'])
a0=np.array(irt.metadata['initial_state_si']);a0=sc.normalize_state(a0);tb=_module('_pipeline_iltt','ILTT/ILTTToolbox.py');x=rec['x_initial'];T=2*np.pi*tb.T_a(x[5],x[4]);duration=T*sc.time_s/DAY_S
raw=tb.get_approx_trajectory_j_dm_v2(a0[:3][None,:],a0[3:][None,:],x[5],x[4],T,0,1,x[1],x[2],x[0],x[3],False,True)
eph=Ephemerides();mission=irt.metadata['mission'];epoch=irt.metadata['epoch_jd']
records=[];items=[]
def add(title,p):
    tr=Trajectory.load(p);m=tr.metadata;model=m.get('bounded_model');line=f"T = {m['mission']['tof_days']:.2f} сут"
    if model:line+=f"; F = {model['a_max']*Scales(**m['scales']).acceleration_m_s2*m['mission']['mass_kg']*1000:.3f} мН\nβ = {model['beta']:.5f}; α = {model['alpha']:g}"
    elif 'departure' in m:line+=f"\nv∞ = {m['departure']['norm_m_s']/1000:.3f} км/с"
    else:line+=f"\nλ = {rec['lambda_corrected']:.5f}"
    items.append((title,line,tr.arrays['r_m']/AU_M,tr.arrays.get('active',np.ones(len(tr.arrays['r_m']),dtype=bool)),np.array(m['target_state_si'])[:3]/AU_M,tr.arrays))
    records.append(dict(title=title,path=str(p),arrays_sha256=sha256(p/'trajectory.npz'),mission=m['mission'],model=model))
arr={'departure_orbit_m':eph.state(mission['departure'],epoch+np.linspace(0,duration,400),'Sun')[:,:3],'target_orbit_m':eph.state(mission['target'],epoch+np.linspace(0,duration,400),'Sun')[:,:3]}
items.append(('Фаза → начальная ветвь ILTT',f"λ = {rec['lambda_initial']:.5f}; k = {rec['k']}\nT = {duration:.2f} сут · приближение",raw['traj']*sc.distance_m/AU_M,np.ones(len(raw['traj']),dtype=bool),eph.state(mission['target'],epoch+duration,'Sun')[:3]/AU_M,arr))
np.savez_compressed(out/'iltt_initial.npz',r_m=raw['traj']*sc.distance_m,t_s=np.linspace(0,T*sc.time_s,len(raw['traj'])))
records.append(dict(title=items[0][0],source=str(run/'stage_irt'/'irt'),x_initial=x,arrays_sha256=sha256(out/'iltt_initial.npz'),derived_tof_days=duration,status='approximation, not an accepted endpoint'))
add('ILTT: согласование → уточнённая ИРТ',run/'stage_irt'/'irt')
cp=json.loads((run/'stage_departure'/'continuation.json').read_text());add('Продолжение отлётного избытка',run/'stage_departure'/cp['last_point'])
if (run/'psi_source').exists():add('Ограниченная тяга: Пазов',run/'psi_source')
if g[nid].get('artifact'):add('Полная масса; ПСИ ещё не достигнута',Path(g[nid]['artifact']))
parent=nid
while True:
    children=[(k,n) for k,n in g.items() if n['request'].get('parent_artifact')==g[parent].get('artifact') and n.get('artifact') and k!=parent]
    if not children:break
    parent,node=children[0];op=node['request']['operation']
    add({'intermediate_release':'Освобождение длительности','physical_continue':'Продолжение к физической ПСИ','release':'Физическая ПСИ: свободное время'}.get(op,op),Path(node['artifact']))
limit=max(float(np.max(np.abs(a[2][:,:2]))) for a in items)*1.10
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
for page in range((len(items)+2)//3):
    columns=min(3,len(items)-page*3);fig,axes=plt.subplots(1,columns,figsize=(5*columns,6.5));axes=np.atleast_1d(axes);fig.subplots_adjust(top=.78,bottom=.18,left=.055,right=.99,wspace=.27)
    for j,ax in enumerate(axes):
        i=3*page+j
        if i>=len(items):ax.axis('off');continue
        title,line,r,active,target,arrays=items[i]
        for key,style in [('departure_orbit_m',':'),('target_orbit_m','--')]:
            if key in arrays:
                orbit=arrays[key]/AU_M;ax.plot(orbit[:,0],orbit[:,1],style,color='.73',lw=1)
        _segments(ax,r,np.asarray(active,dtype=bool));ax.scatter(0,0,c='#ffaa18',s=45,zorder=5)
        ax.scatter(*r[0,:2],c='#1765d1',s=42,zorder=6);ax.scatter(*target[:2],c='#d62925',s=42,zorder=6)
        ax.scatter(*r[-1,:2],marker='x',color='k',s=55,zorder=7)
        ax.set_title(f'{i+1}. {title}\n{line}',fontsize=11,pad=10)
        ax.set(xlim=(-limit,limit),ylim=(-limit,limit),xlabel='x, а.е.',ylabel='y, а.е.');ax.set_aspect('equal');ax.grid(alpha=.18)
        ax.spines[['top','right']].set_visible(False)
    handles=[Line2D([],[],color='k',lw=2,label='Тяга включена'),Line2D([],[],color='k',ls='--',label='Тяга выключена'),Line2D([],[],color='#1765d1',marker='o',ls='',label='Земля, старт'),Line2D([],[],color='#d62925',marker='o',ls='',label='Марс, прибытие'),Line2D([],[],color='k',marker='x',ls='',label='КА, конец')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.015),ncol=5,fontsize=11)
    fig.savefig(out/f'steps_{page+1}.png',dpi=170);fig.savefig(out/f'steps_{page+1}.svg');plt.close(fig);preview_jpeg(out/f'steps_{page+1}.png',out/f'steps_{page+1}.jpg')
(out/'sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
from PIL import Image
for p in out.glob('*.jpg'):
    im=Image.open(p);print(str(p),im.format,im.size,p.stat().st_size)

