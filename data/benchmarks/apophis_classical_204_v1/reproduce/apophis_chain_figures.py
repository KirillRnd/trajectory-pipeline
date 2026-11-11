import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image
from trajectory_pipeline.data import Trajectory,AU_M,write_json,sha256
root=Path('runs/apophis_classical_204/chain_july_final')
audit=json.loads((root/'independent_chain_audit.json').read_text())
items=[Trajectory.load(r['artifact']) for r in audit]+[Trajectory.load(root/'05_free_time')]
out=Path('output/pipeline/apophis_classical_204');out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
titles=['1. ILTT → проверенная ИРТ','2. Продолжение по добавочному импульсу','3. Пазов: постоянная масса','4. ПСИ: переменная масса','5. ПСИ: освобождена длительность']
def draw(ax,trajectory,title):
    a=trajectory.arrays;m=trajectory.metadata;r=a['r_m']/AU_M
    for key,color in [('departure_orbit_m','.72'),('target_orbit_m','#d79e9e')]:
        curve=a[key]/AU_M;ax.plot(curve[:,0],curve[:,1],color=color,lw=.8)
    active=np.asarray(a.get('active',np.ones(len(r))),dtype=bool)
    boundaries=np.r_[0,np.flatnonzero(active[1:]!=active[:-1])+1,len(r)-1]
    for p,q in zip(boundaries[:-1],boundaries[1:]):ax.plot(r[p:q+1,0],r[p:q+1,1],color='black',lw=1.8,ls='-' if active[p] else '--')
    ax.scatter(0,0,color='#ff9c00',s=35,zorder=5)
    ax.scatter(*r[0,:2],color='#1260d8',s=35,zorder=5)
    target=np.asarray(m['target_state_si'])[:3]/AU_M;ax.scatter(*target[:2],color='#d52323',s=35,zorder=5)
    days=m['mission']['tof_days'];vinf=m.get('departure',{}).get('norm_m_s',0)/1000
    subtitle=f'T = {days:.2f} сут; v∞ = {vinf:.2f} км/с'
    if m['stage']=='psi':subtitle+=f"; Xe = {m['verification']['fuel_kg']:.2f} кг"
    ax.set_title(title+'\n'+subtitle,fontsize=11,pad=10)
    ax.set(xlabel='x, а.е.',ylabel='y, а.е.',xlim=(-1.45,1.45),ylim=(-1.45,1.45));ax.set_aspect('equal');ax.grid(alpha=.2)
    ax.spines[['right','top']].set_visible(False)
handles=[Line2D([],[],color='black',label='Активный участок'),Line2D([],[],color='black',ls='--',label='Пассивный участок'),Line2D([],[],color='#1260d8',marker='o',ls='',label='Земля, старт'),Line2D([],[],color='#d52323',marker='o',ls='',label='Апофис, прибытие')]
records=[]
for name,indices in [('01_iltt_departure',[0,1]),('02_pazov_psi',[2,3]),('03_duration',[3,4])]:
    fig,axes=plt.subplots(1,2,figsize=(12.8,6.4))
    for ax,i in zip(axes,indices):draw(ax,items[i],titles[i])
    fig.suptitle('Земля → Апофис, 01.07.2029 · 204 кг / сухая 140 кг · 2 СПД-50М',fontsize=14,y=.98)
    fig.legend(handles=handles,loc='lower center',ncol=4,frameon=False,fontsize=10)
    fig.subplots_adjust(top=.83,bottom=.14,wspace=.22)
    fig.savefig(out/(name+'.png'),dpi=180);fig.savefig(out/(name+'.svg'))
    im=Image.open(out/(name+'.png')).convert('RGB');im.thumbnail((1280,1280));p=out/(name+'.jpg');im.save(p,quality=85,optimize=True)
    assert p.stat().st_size<200*1024
    records.append(dict(path=str(p),format=Image.open(p).format,size=im.size,bytes=p.stat().st_size,sha256=sha256(p)));plt.close(fig)
write_json(out/'manifest.json',records)
for i,t in enumerate(items):
    print(titles[i],t.metadata['mission']['tof_days'],t.metadata.get('functional_dimensionless'),t.metadata.get('verification',{}).get('fuel_kg'),flush=True)
