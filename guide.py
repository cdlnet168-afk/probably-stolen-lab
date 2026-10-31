"""Probably Stolen game-only community recipe planner; no real chemistry model."""
import math
from fractions import Fraction
from engine import num

def plan(d):
    rid=d['recipe']
    if rid not in ['dream','nightmare','caffeine','phanta','nomore','zyanide','birth']:raise ValueError('未知配方')
    amount=num(d['amount'],'光谱仪有效原料量',.000001)
    existing=num(d.get('existing',0),'已有目标有效成分')
    modules=num(d.get('modules',4),'成型模组数',0)
    if not modules.is_integer():raise ValueError('模组数必须为整数')
    additions=[]
    def add(name,active,key,default):
        pct=num(d.get(key,default),name+'浓度',.000001,100)
        additions.append(dict(name=name,active_ml=active,percent=pct,stock_ml=active*100/pct))
    if rid in ['dream','nightmare','caffeine']:
        factor=1 if rid=='caffeine' else 5
        present=num(d.get('solvent',0),'已有有效酒精')
        add('酒精',max(0,amount*factor-present),'alcohol_pct',70)
        expected=amount*(.75 if rid=='caffeine' else .5)+existing
    elif rid=='phanta':
        add('还原剂',amount*.75,'reducer_pct',95);expected=amount*.1+existing
    elif rid=='nomore':
        add('还原剂',amount,'reducer_pct',95);add('脂合剂',amount*.25,'lipo_pct',95);expected=amount*.6+existing
    else:expected=amount
    portion={'dream':2,'nightmare':4,'caffeine':5,'phanta':.5,'nomore':4,'zyanide':.6,'birth':.1}[rid]
    pollution=[12,6,3,1,0][min(int(modules),4)]
    return dict(additions=additions,expected_active_ml=expected,portion=portion,pure_equivalent_count=math.floor(round(expected/portion,9)),remainder_active_ml=expected%portion,max_percent=100-pollution,warning='理论量按搅拌后有效原料计算，未含提纯/热损耗及逐次取整；瓶数为100%干净原料的等效数，最终请使用成品计算。加入的试剂剩余部分未必全是水。')

def clean(d):
    target=d['target'];amount=num(d['amount'],'要去除的有效成分mL')
    ratio={'protein':1,'fat':.125,'acid':1,'base':1}.get(target)
    if ratio is None:raise ValueError('稳定剂没有固定总消耗比，请分次加入后重扫')
    pct=num(d.get('stock',95),'原液浓度',.000001,100)
    step=num(d.get('step',.1),'工具刻度',.000001)
    active=amount*ratio
    # Dilute to a tool-aligned final dose without rounding up active reagent.
    stock=active*100/pct;dose=math.ceil(round(stock/step,10))*step
    # Search rational recipes with stock, water and dose all on the requested grid.
    # No rounding of effective reagent is permitted. If no practical exact recipe
    # is found, show the unaligned solution explicitly rather than promising it.
    working=min(10,pct)
    working_dose=active*100/working
    prep_stock=max(10,math.ceil(round(stock/step,10))*step)
    prep_total=prep_stock*pct/working
    aligned=False
    if active == 0:
        return dict(status='no_action',message='当前目标量为0，不需要加入试剂。')
    units=Fraction(str(amount))*Fraction(str(ratio))/(Fraction(str(pct))/100*Fraction(str(step)))
    u,v=units.numerator,units.denominator
    n0=max(1,math.ceil(working_dose/step-1e-10))
    k0=max(1,math.ceil(stock/step-1e-10))
    best=None
    for k in range(k0,k0+200):
        for n in range(n0,n0+500):
            product=k*n*v
            if product % u:continue
            total=product//u
            if total<max(k,n) or total*step>5000:continue
            score=total+2*n+.01*k
            if best is None or score<best[0]:best=(score,k,n,total)
    if best:
        _,k,n,total=best
        prep_stock=k*step;prep_total=total*step;working_dose=n*step
        working=pct*k/total;aligned=True
    return dict(status='estimate',aligned=aligned,working_dose_ml=working_dose,prep_pct=working,prep_stock_ml=prep_stock,prep_total_ml=prep_total,prep_water_ml=prep_total-prep_stock,prep_leftover_ml=prep_total-working_dose,ratio=ratio,active_ml=active,stock_ml=stock,dose_ml=dose,water_ml=max(0,dose-stock),working_pct=active/dose*100 if dose else 0,source='BWIKI 进阶化学，2026-11-01；社区机制，非个人实验校准',warning='按单一目标、无竞争反应估算。蛋白质/脂肪等同时存在会改变消耗；先少量处理再重扫。原液和水的量取也要达到显示精度，否则扩大配制批量。')
