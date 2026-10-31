import math, statistics

def num(v,name,low=0,high=None):
    try: x=float(v)
    except (TypeError,ValueError): raise ValueError(name+'必须是数字')
    if not math.isfinite(x) or x<low or (high is not None and x>high): raise ValueError(name+'超出范围')
    return x

def dilution(d):
    c=num(d['stock'],'原液浓度',0,100)/100;t=num(d['target'],'目标浓度',0,100)/100;b=num(d.get('diluent',0),'稀释液浓度',0,100)/100
    v=num(d['volume'],'体积',0.0000001)
    if abs(c-b)<1e-12: raise ValueError('原液和稀释液浓度相同，无法计算唯一配比')
    f=(t-b)/(c-b)
    if f<=0 or f>1: raise ValueError('目标浓度应在两种液体浓度之间，且包含原液')
    if d.get('mode')=='stock': a=v; total=a/f; water=total-a
    else: total=v;a=total*f;water=total-a
    return dict(stock_ml=a,diluent_ml=water,final_ml=total,active_ml=total*t,formula='V原=C差目标/C差原 × V终；默认体积可加、混合时无反应')

def mixing(d):
    rows=d['rows'];total=0;amount={}
    if not rows: raise ValueError('至少输入一种液体')
    for row in rows:
        v=num(row['volume'],'液体体积',0.0000001);total+=v;s=0
        for k,val in row['components'].items():
            p=num(val,k+'浓度',0,100);s+=p;amount[k]=amount.get(k,0)+v*p/100
        if s>100.000001: raise ValueError('同一液体的组分百分比合计不能超过100%')
        amount['未指定余量']=amount.get('未指定余量',0)+v*(100-s)/100
    return dict(total_ml=total,components=[dict(name=k,ml=v,percent=v/total*100) for k,v in amount.items() if v>1e-10],warning='仅混合守恒；不自动模拟酸碱反应、沉淀或蒸发。')

def validate_experiment(d):
    for k in ['target','reagent','version','context']: 
        if not str(d.get(k,'')).strip(): raise ValueError('填写目标、试剂、版本和条件分组')
    for k in ['before_total','after_total']:num(d[k],k,0.0000001)
    for k in ['before_pct','after_pct','reagent_pct']:num(d[k],k,0,100)
    if num(d['dose'],'添加体积',0.0000001)<=0: raise ValueError('剂量必须大于0')
    if d.get('residual') not in [None,'']:
        r=num(d['residual'],'剩余试剂');added=float(d['dose'])*float(d['reagent_pct'])/100
        if r>added+1e-9:raise ValueError('剩余有效试剂不能大于添加量；若原液本来有试剂，请另分组记录')
    if float(d.get('rounding',0.01))<=0:raise ValueError('测量精度应大于0')
    num(d.get('temperature',26),'温度',-273.15,10000)
    num(d.get('rounding',.01),'测量精度',0.000000001)
    for field in ['before_components','after_components']:
        raw=d.get(field,'')
        if raw:
            parts={}
            for pair in raw.replace('，',',').split(','):
                a=pair.replace('：',':').split(':')
                if len(a)!=2 or not a[0].strip():raise ValueError('完整组分格式应为 成分:百分比,成分:百分比')
                if a[0].strip() in parts:raise ValueError('组分名称重复')
                parts[a[0].strip()]=num(a[1],'组分浓度',0,100)
            if sum(parts.values())>100.000001:raise ValueError('完整组分合计超过100%')
            d[field+'_parsed']=parts
    return d

def predict(d,records):
    target=num(d['amount'],'待去除量',0.0000001);conc=num(d['concentration'],'试剂浓度',0.0000001,100)/100
    step=num(d.get('step',0.1),'量具步长',0.0000001)
    matching=[r for r in records if all(str(r.get(k,''))==str(d.get(k,'')) for k in ['target','reagent','version','context']) and float(r.get('temperature',26))==float(d.get('temperature',26))]
    ratios=[];bounds=[];removed=[]
    for r in matching:
        if not r.get('usable',True):continue
        before=float(r['before_total'])*float(r['before_pct'])/100;after=float(r['after_total'])*float(r['after_pct'])/100
        delta=before-after;active=float(r['dose'])*float(r['reagent_pct'])/100
        if delta<=0:continue
        if r.get('residual') not in [None,'']:
            consumed=active-float(r['residual'])
            if consumed<=0:continue
            ratios.append(consumed/delta);removed.append(delta)
        elif after>float(r.get('rounding',.01)) and r.get('completed'):
            ratios.append(active/delta);removed.append(delta)
        else:bounds.append(active/delta)
    if not ratios:
        return dict(status='insufficient',message='没有同版本、同条件的可用定量记录。终点为0且未测剩余试剂的实验只能提供上界，不能算刚好用量。',matches=len(matching),upper_ratio=min(bounds) if bounds else None)
    ratio=statistics.median(ratios);low=min(ratios);high=max(ratios);dose=target*ratio/conc
    spread=(high-low)/ratio if ratio else 0
    return dict(status='estimate',samples=len(ratios),ratio=ratio,active_ml=target*ratio,dose_ml=dose,range_ml=[target*low/conc,target*high/conc],rounded_ml=math.ceil((dose-1e-12)/step)*step,concentration=conc*100,extrapolated=target<min(removed) or target>max(removed),inconsistent=spread>.2,quality='单次标定' if len(ratios)==1 else ('数据分歧较大' if spread>.2 else '同条件经验估计'),warning='经验线性模型，不是已证实的游戏化学方程。显示范围为已测比例范围，不是统计置信区间。',matches=len(matching))

def finishing(d):
    v=num(d['volume'],'溶液体积',0.0000001);p=num(d['purity'],'有效成分',0,100);water=num(d.get('water',0),'水',0,100)
    alcohol=num(d.get('alcohol',0),'酒精',0,100);lipo=num(d.get('lipobond',0),'脂合剂',0,100)
    if p+water+alcohol+lipo>100.000000001:raise ValueError('有效成分、水、酒精和脂合剂浓度合计超过100%')
    modules=num(d['modules'],'模组数量',0)
    if not modules.is_integer():raise ValueError('模组数量必须是整数')
    count=int(modules);portion=num(d['portion'],'每件用量',0.0000001)
    pollution=[12,6,3,1,0][min(count,4)];actual=p*(1-pollution/100)
    grade=next((name for floor,name in [(99,'实验室纯'),(90,'药用级'),(80,'近药用级'),(60,'街头标准'),(45,'掺兑级'),(30,'垃圾级'),(0,'淀粉级')] if actual>=floor),'淀粉级')
    pieces=math.floor(round(v/portion,10));blocked=v*(water+alcohol+lipo)/100>0.100000001
    return dict(count=0 if blocked else pieces,potential_count=pieces,remainder=v if blocked else max(0,v-pieces*portion),solvent_ml=v*(water+alcohol+lipo)/100,active_percent=actual,grade=grade,blocked=blocked,pollution= pollution,warning='社区模型：加工把一部分有效成分替换为物理杂质；最终以游戏实物为准。水、酒精、脂合剂合计≤0.1mL才能成型；99%等级依据社区资料，须核对实物。')


def neutralization(d,records):
    unit=d.get('input_unit','ml')
    current=num(d['current'],'当前目标量',0)
    if unit=='percent':
        current=num(d['current'],'目标浓度',0,100)*num(d['solution_volume'],'溶液总体积',0.0000001)/100
    elif unit!='ml':raise ValueError('未知输入单位')
    remaining=num(d.get('remaining',0),'希望剩余量',0)
    if remaining>current:raise ValueError('希望剩余量不能大于当前量')
    removed=current-remaining
    if removed<=1e-12:return dict(status='no_action',current_ml=current,remove_ml=0,message='已经达到目标，不需要加试剂。')
    stock=num(d['stock'],'原液浓度',0.0000001,100)
    step=num(d.get('step',.1),'量具步长',.0000001)
    if d.get('ratio_mode')=='manual':
        ratio=num(d.get('ratio'),'实测消耗系数',.0000001)
        if not str(d.get('ratio_source','')).strip():raise ValueError('手动比例必须填写实测依据；不能默认1:1')
        estimate=dict(ratio=ratio,quality='手动实测比例',warning='本结果依赖你输入的实测消耗比例，不代表已验证的游戏反应方程。',samples=0,range_ml=None)
    else:
        estimate=predict(dict(d,amount=removed,concentration=100),records)
        if estimate['status']=='insufficient':return dict(estimate,current_ml=current,remove_ml=removed)
        ratio=estimate['ratio']
    active=removed*ratio
    if d.get('prepare_mode')=='dose':
        dose=num(d['desired_dose'],'希望加液量',.0000001);working=active/dose*100
        if working>stock+1e-10:raise ValueError('加液量太小：需要浓度超过现有原液。请增加加液量，或用更浓的原液。')
    else:
        working=num(d['working'],'工作液浓度',.0000001,100)
        if working>stock:raise ValueError('工作液浓度高于原液，不能通过加水配出')
        dose=active/(working/100)
    # Prepare a stock batch large enough for the dose. Rounding applies to batch only, not reaction dose.
    batch=num(d.get('batch',dose) or dose,'配制总量',.0000001)
    if batch+1e-10<dose:raise ValueError('配制总量小于本次所需加液量，请增加配制总量')
    mix=dilution(dict(stock=stock,target=working,diluent=0,volume=batch))
    lower=math.floor((dose+1e-12)/step)*step;upper=math.ceil((dose-1e-12)/step)*step
    # Offer a dosing volume aligned with the measuring step, with concentration adjusted to preserve active amount.
    aligned=max(step,upper);aligned_c=active/aligned*100
    direct_stock=active/(stock/100)
    warnings=[estimate['warning'],'蛋白质去除可能是沉淀／过滤而非简单中和；本页只计算标定过的目标消耗。','稀释水假定为0%该试剂且不参与反应；含其他活性组分时不能直接套用。','显示为0不等于真实绝对为0，达到终点后仍应检测目标与剩余试剂。']
    if estimate.get('extrapolated'):warnings.append('本次去除量超出已测范围，属于外推。')
    if estimate.get('inconsistent'):warnings.append('实验比例分歧较大，请先复核条件。')
    return dict(status='estimate',current_ml=current,remaining_ml=remaining,remove_ml=removed,ratio=ratio,active_ml=active,stock=stock,working=working,dose_ml=dose,batch_ml=batch,stock_ml=mix['stock_ml'],water_ml=mix['diluent_ml'],leftover_ml=max(0,batch-dose),rounded_down_ml=lower,rounded_up_ml=upper,rounded_down_remaining=max(remaining,current-lower*working/100/ratio),rounded_up_excess=max(0,upper*working/100-active),aligned_dose_ml=aligned,aligned_concentration=aligned_c,aligned_stock_ml=direct_stock,aligned_water_ml=max(0,aligned-direct_stock),quality=estimate['quality'],samples=estimate.get('samples',0),warnings=warnings)
