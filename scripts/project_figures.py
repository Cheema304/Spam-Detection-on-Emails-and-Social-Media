from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web'/'static'/'charts'
OUT.mkdir(parents=True,exist_ok=True)

# Risk matrix from project risk register
prob_map={'Low':1,'Medium':2,'High':3}
impact_map={'Low':1,'Medium':2,'High':3}
rows=[]
with (ROOT/'docs'/'risk_register.csv').open(encoding='utf-8') as f:
    rows=list(csv.DictReader(f))
fig,ax=plt.subplots(figsize=(7,5.8))
xs=[prob_map[r['Probability']] for r in rows]
ys=[impact_map[r['Impact']] for r in rows]
ax.scatter(xs,ys,s=110,alpha=.8)
for x,y,r in zip(xs,ys,rows):
    ax.annotate(r['Risk ID'],(x,y),xytext=(5,5),textcoords='offset points',fontsize=8,fontweight='bold')
ax.set_xticks([1,2,3],['Low','Medium','High'])
ax.set_yticks([1,2,3],['Low','Medium','High'])
ax.set_xlim(.5,3.5);ax.set_ylim(.5,3.5)
ax.set_xlabel('Probability');ax.set_ylabel('Impact')
ax.set_title('Project Risk Matrix',fontweight='bold')
ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(OUT/'risk_matrix.png',dpi=170,bbox_inches='tight');plt.close(fig)

# Weeks 1-5 assessment timeline
items=[
('Project Charter & Stakeholders',1,1),
('Business & Problem Analysis',2,1),
('Requirements Elicitation',3,1),
('SRS & Acceptance Criteria',4,1),
('Feasibility & Risk Analysis',5,1),
('GitHub + Jira Evidence',1,5),
]
fig,ax=plt.subplots(figsize=(10,5.5))
y=np.arange(len(items))
for idx,(label,start,duration) in enumerate(items):
    ax.barh(idx,duration,left=start-.5,height=.55)
ax.set_yticks(y,[x[0] for x in items]);ax.invert_yaxis()
ax.set_xticks([1,2,3,4,5],[f'Week {i}' for i in range(1,6)])
ax.set_xlim(.5,5.5);ax.set_xlabel('Assessment 1 Timeline')
ax.set_title('Weeks 1–5 Delivery Plan',fontweight='bold')
ax.grid(axis='x',alpha=.25)
fig.tight_layout();fig.savefig(OUT/'assessment_timeline.png',dpi=170,bbox_inches='tight');plt.close(fig)
print('Generated risk_matrix.png and assessment_timeline.png')
