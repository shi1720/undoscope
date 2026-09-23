#!/usr/bin/env python3
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper/figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'ps.fonttype':42,'axes.labelcolor':'#243447','text.color':'#172b4d'})
COLORS={'snapshot':'#b24b43','mapped':'#db8d3c','value':'#9575ad','object':'#657b91','field':'#537da5','undoscope':'#008577','deny':'#999999'}
LABELS={'snapshot':'Snapshot','mapped':'Mapped inverse','value':'Value guard','object':'Object guard','field':'Component guard','undoscope':'UndoScope','deny':'Deny all'}
def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight');fig.savefig(OUT/(name+'.png'),dpi=200,bbox_inches='tight');plt.close(fig)

def frontier():
    data=json.loads((ROOT/'results/exhaustive-summary.json').read_text())['summary']
    fig,ax=plt.subplots(figsize=(6.6,3.65))
    for p,r in data.items():
        x=100*r['collateral']/r['cases'];y=100*r['recovered']/r['eligible']
        ax.scatter(x,y,s=75 if p=='undoscope' else 45,color=COLORS[p],zorder=3)
        offsets={'undoscope':(10,-5),'object':(10,1),'field':(10,4),'deny':(10,-12),'mapped':(8,0),'value':(8,0),'snapshot':(-58,8)}
        ax.annotate(LABELS[p],(x,y),xytext=offsets[p],textcoords='offset points',fontsize=8)
    ax.set(xlabel='Histories with collateral mutation (%)',ylabel='Eligible histories safely recovered (%)',xlim=(-3,83),ylim=(-7,106))
    ax.grid(alpha=.17);save(fig,'01-safety-recovery')

def heatmap():
    rows=list(csv.DictReader((ROOT/'results/exhaustive.csv').open()))
    policies=list(LABELS);kinds=['set','add','grant','create']
    fig,axes=plt.subplots(1,2,figsize=(7,3.3))
    for ax,metric,title in zip(axes,['collateral','recovered'],['Collateral histories (%)','Eligible recoveries (%)']):
        values=np.zeros((len(policies),4))
        for i,p in enumerate(policies):
            for j,k in enumerate(kinds):
                part=[r for r in rows if r['policy']==p and r['kind']==k]
                denominator=len(part) if metric=='collateral' else sum(r['eligible']=='True' for r in part)
                values[i,j]=100*sum(r[metric]=='True' for r in part)/denominator
        im=ax.imshow(values,vmin=0,vmax=100,cmap='Reds' if metric=='collateral' else 'YlGnBu',aspect='auto')
        for i in range(len(policies)):
            for j in range(4):
                ax.text(j,i,f'{values[i,j]:.0f}',ha='center',va='center',color='white' if values[i,j]>55 else '#172b4d',fontsize=8)
        ax.set_xticks(range(4),['Register','Counter','Grant','Create'],rotation=20)
        ax.set_yticks(range(len(policies)),[LABELS[p] for p in policies] if ax is axes[0] else [])
        ax.set_title(title,fontsize=10)
    fig.tight_layout();save(fig,'02-domain-results')

def architecture():
    fig,ax=plt.subplots(figsize=(7,3));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
    def box(x,y,w,h,text,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',linewidth=.8,edgecolor=color,facecolor=color+'12'))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8)
    box(.15,2.25,2.2,1.05,'Untrusted recovery planner\nLLM + tool-result prose','#b24b43')
    box(3.15,2.25,3.45,1.05,'Trusted recovery boundary\nreceipt + authenticated scope','#008577')
    box(7.45,2.25,2.2,1.05,'Domain adapter\noperation semantics','#537da5')
    box(3.15,.25,6.5,1.15,'One atomic database transaction\ncurrent policy + expiry + incarnation + effect evidence\ninverse + receipt consumption + audit commit','#008577')
    for a,b in [((2.45,2.78),(3.0,2.78)),((6.72,2.78),(7.3,2.78)),((8.55,2.12),(8.55,1.53))]:
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color='#536577'))
    ax.text(.15,.73,'Model chooses a handle.\nHost binds identity.\nAdapter derives the inverse.',fontsize=8)
    save(fig,'03-boundary')

def ambiguity():
    fig,axes=plt.subplots(2,1,figsize=(3.45,2.5),sharex=True)
    for ax,peer,title in zip(axes,[False,True],['History A: no intervening writer','History B: independent same-value write']):
        ax.set(xlim=(-.35,3.4),ylim=(-.4,.5));ax.axis('off');ax.set_title(title,loc='left',fontsize=9)
        values=['open','triage','triage','open' if not peer else 'triage']
        labels=['initial','agent\neffect','peer\nconfirms' if peer else 'no new\nwrite','required\nresult']
        for i,(v,l) in enumerate(zip(values,labels)):
            color='#008577' if i==3 else '#537da5'
            ax.text(i,.18,v,ha='center',color=color,fontweight='bold',fontsize=10)
            ax.text(i,-.10,l,ha='center',fontsize=8)
            if i<3: ax.annotate('',(i+.75,.18),(i+.26,.18),arrowprops={'arrowstyle':'->','color':'#8190a0'})
    fig.tight_layout();save(fig,'04-indistinguishable-values')

def latency():
    rows=list(csv.DictReader((ROOT/'results/latency.csv').open()));policies=list(LABELS)[:-1]
    fig,ax=plt.subplots(figsize=(3.45,2.5))
    for i,p in enumerate(policies):
        vals=sorted(float(r['microseconds']) for r in rows if r['policy']==p)
        ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),label={'snapshot':'Snapshot','mapped':'Mapped','value':'Value','object':'Object','field':'Component','undoscope':'UndoScope'}[p],color=COLORS[p],lw=1.3)
    ax.set(xlabel='Recovery transaction latency (microseconds)',ylabel='Empirical CDF',xlim=(0,300))
    ax.legend(fontsize=6.5,ncol=2,loc='lower right');ax.tick_params(labelsize=7);ax.xaxis.label.set_size(8);ax.yaxis.label.set_size(8);ax.grid(alpha=.15);save(fig,'05-latency')

def models():
    path=ROOT/'results/model-summary.json'
    if not path.exists():return
    data=json.loads(path.read_text())['groups']
    fig,ax=plt.subplots(figsize=(3.45,2.5))
    cells=[('gpt-4.1-mini-2025-04-14',False),('gpt-4.1-mini-2025-04-14',True),('gpt-4.1-2025-04-14',False),('gpt-4.1-2025-04-14',True)]
    for i,(model,hardened) in enumerate(cells):
        for j,policy in enumerate(['mapped','undoscope']):
            r=next(x for x in data if x['model']==model and x['hardened']==hardened and x['policy']==policy)
            x=i*2.3+j*.75
            ax.bar(x,r['collateral'],color=COLORS[policy],width=.65,label=LABELS[policy] if i==0 else None)
            ax.text(x,r['collateral']+.4,str(r['collateral']),ha='center',fontsize=7)
    ax.set_xticks([i*2.3+.375 for i in range(4)],['Mini\nordinary','Mini\nhardened','4.1\nordinary','4.1\nhardened'])
    ax.tick_params(labelsize=7);ax.set_ylim(0,20);ax.legend(fontsize=6.5,loc='upper center',ncol=2)
    ax.set_ylabel('Collateral outcomes / 60 tasks',fontsize=8)
    fig.tight_layout();save(fig,'06-model-replay')
if __name__=='__main__':
    frontier();heatmap();architecture();ambiguity();latency();models()
