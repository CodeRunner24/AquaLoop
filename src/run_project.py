"""AquaLoop AI: reproducible synthetic building digital twin, ML and policy benchmark.
No physical plant is connected. All parameters are illustrative assumptions.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; OUT=ROOT/'outputs'; DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
RNG=np.random.default_rng(2026)
N_DAYS=90; N=N_DAYS*24

def generate():
    t=np.arange(N); hour=t%24; dow=(t//24)%7
    occupancy=np.clip(.68 + .12*np.sin(2*np.pi*t/(24*7)+.7)+RNG.normal(0,.065,N),.38,.96)
    # Separate physical streams: total metered use, collectable greywater, non-potable demand.
    profile=0.48+1.03*np.exp(-((hour-8)/2.35)**2)+.88*np.exp(-((hour-21)/2.6)**2)
    water_total=2.7*profile*(.55+.72*occupancy)*np.clip(RNG.normal(1,.09,N),.72,1.32)
    greywater=water_total*(.37+.055*np.sin(2*np.pi*(hour-4)/24))
    greywater=np.clip(greywater,0,None)
    reuse_demand=water_total*(.25+.055*np.exp(-((hour-9)/4)**2))
    wastewater_temp=24+5*np.exp(-((hour-8)/3.2)**2)+4*np.exp(-((hour-21)/3.4)**2)+RNG.normal(0,.45,N)
    inlet_temp=13+2.5*np.sin(2*np.pi*t/(24*90))
    tariff=np.where((hour>=17)&(hour<22),4.2,np.where((hour>=7)&(hour<17),2.65,1.65))
    df=pd.DataFrame({'hour_index':t,'hour_of_day':hour,'weekday':dow,'occupancy':occupancy,
        'total_water_m3':water_total,'greywater_in_m3':greywater,
        'nonpotable_demand_m3':reuse_demand,'wastewater_temp_c':wastewater_temp,
        'cold_inlet_temp_c':inlet_temp,'electricity_tariff_tl_kwh':tariff})
    return df


def features(df):
    h=df.hour_of_day.values
    return pd.DataFrame({'h_sin':np.sin(2*np.pi*h/24),'h_cos':np.cos(2*np.pi*h/24),
        'w_sin':np.sin(2*np.pi*df.weekday.values/7),'w_cos':np.cos(2*np.pi*df.weekday.values/7),
        'occupancy':df.occupancy.values})


def simulate(df, mode, capacity=20.0, treatment_capacity=2.2, heat_eff=.45):
    """Safety gate must be externally certified; simulation assumes quality_ok=True unless fault injected.
    greywater volume in m3/h; kWh heat= m3*1000 kg/m3*4.186 kJ/kg C*deltaT /3600.
    Baseline is conventional reuse with reactive pump dispatch, smart is predictive water dispatch.
    """
    raw=capacity*.35*.6; clean=capacity*.35*.4
    raw_cap=capacity*.6; clean_cap=capacity*.4
    totals={'reuse_m3':0., 'water_m3':0.,'treated_m3':0.,'heat_kwh':0.,'pump_kwh':0.,'untreated_discharge_m3':0.,'overflow_m3':0.}
    timeline=[]
    for i,r in df.reset_index(drop=True).iterrows():
        inflow=float(r.greywater_in_m3); need=float(r.nonpotable_demand_m3)
        temp=float(r.wastewater_temp_c); cold=float(r.cold_inlet_temp_c)
        quality_ok=bool(r.get('quality_ok',True))
        raw+=inflow
        overflow=max(0,raw-raw_cap); raw=min(raw,raw_cap)
        # Gated separation of untreated raw reservoir and treated clean reservoir.
        if mode=='conventional':
            target=treatment_capacity*(.8 if 6<=int(r.hour_of_day)<=22 else .3)
        else:
            forecast=float(r.get('forecast_nonpotable_m3',need))
            future=float(df.iloc[min(i+1,len(df)-1)].get('forecast_nonpotable_m3',forecast))
            target=min(treatment_capacity,max(0.05,forecast*1.12+max(0,future-forecast)*.15))
        treatment=min(treatment_capacity,raw,max(0,clean_cap-clean),target) if quality_ok else 0.
        raw-=treatment; clean+=treatment
        reuse=min(need,clean) if quality_ok else 0.
        clean-=reuse
        # Heat recovery is a theoretical thermal potential, not delivered useful heat.
        heat=max(0,inflow*1000*4.186*(temp-cold)*heat_eff/3600)
        pump=treatment*.48+(.14 if treatment>.02 else 0.)
        totals['reuse_m3']+=reuse
        totals['water_m3']+=float(r.total_water_m3)
        totals['treated_m3']+=treatment
        totals['heat_kwh']+=heat
        totals['pump_kwh']+=pump
        totals['overflow_m3']+=overflow
        timeline.append({'hour':i,'fresh_saved_m3':reuse,'pump_kwh':pump,'heat_kwh':heat,
                         'raw_storage_m3':raw,'clean_storage_m3':clean,'storage_m3':raw+clean,
                         'greywater_m3':inflow,'nonpotable_demand_m3':need})
    return totals,pd.DataFrame(timeline)


def main():
    df=generate()
    split=60*24
    f=features(df)
    target=df.nonpotable_demand_m3.values
    reg=RandomForestRegressor(n_estimators=90,max_depth=12,min_samples_leaf=3,n_jobs=-1,random_state=17)
    reg.fit(f.iloc[:split],target[:split]); pred=reg.predict(f)
    # Data leakage avoidance: model is trained only on first 60 days.
    maem=mean_absolute_error(target[split:],pred[split:]); naive=np.full(len(target)-split,target[:split].mean())
    baseline_mae=mean_absolute_error(target[split:],naive)
    df['forecast_nonpotable_m3']=pred
    # Reference fault-detection exercise with a documented injected leak during evaluation.
    meter=df.total_water_m3.to_numpy().copy()
    leak_start=72*24+4; leak_end=72*24+17
    meter[leak_start:leak_end]+=2.8
    det_train=np.column_stack([meter[:split],df.occupancy.values[:split],np.sin(2*np.pi*df.hour_of_day.values[:split]/24),np.cos(2*np.pi*df.hour_of_day.values[:split]/24)])
    det_eval=np.column_stack([meter,df.occupancy.values,np.sin(2*np.pi*df.hour_of_day.values/24),np.cos(2*np.pi*df.hour_of_day.values/24)])
    anomaly=IsolationForest(n_estimators=180,contamination=.025,random_state=21)
    anomaly.fit(det_train); outliers=anomaly.predict(det_eval)==-1
    detected=int(outliers[leak_start:leak_end].sum()); fp=int(outliers[split:][np.r_[0:leak_start-split,leak_end-split:len(outliers)-split]].sum())
    # Comparison only held-out final 30 days.
    holdout=df.iloc[split:].copy().reset_index(drop=True)
    conv,conv_t=simulate(holdout,'conventional')
    smart,smart_t=simulate(holdout,'smart')
    # No recovery base: all nonpotable water supplied from mains; no heat reuse.
    results={'metadata':{'dataset':'synthetic','seed':2026,'training_days':60,'test_days':30,'plant_connected':False,
                         'water_model':'two simplified raw/treated tanks; certified water treatment not modeled',
                         'heat_recovery':'theoretical upper-bound based on efficiency assumption; no heat demand cap'},
      'forecast':{'random_forest_test_mae_m3_h':round(maem,4),'training_mean_test_mae_m3_h':round(baseline_mae,4)},
      'anomalies':{'injected_leak_hours':leak_end-leak_start,'flagged_leak_hours':detected,'false_alarm_hours_outside_leak_test':fp},
      'assumptions':{'tank_m3':20,'treatment_m3_h':2.2,'heat_recovery_efficiency':.45,'pump_specific_kwh_per_m3':.48,
                     'water_price_tl_per_m3':65,'heat_value_tl_per_kwh':1.6,
                     'notes':'illustrative prices only, exclude capex maintenance treatment electricity heat-pump and hygiene monitoring costs'},
      'comparison':{'no_recovery':{'freshwater_m3':round(holdout.total_water_m3.sum(),1),'heat_kwh':0,'pump_kwh':0},
                    'conventional':{k:round(v,2) for k,v in conv.items()},
                    'smart':{k:round(v,2) for k,v in smart.items()}},
      'constraints':['greywater separate from sewage/blackwater','non-potable use only after certified treatment/monitoring','failure diverts to sewage and municipal backup','no automatic potable cross-connection']}
    df.to_csv(DATA/'synthetic_building_90d_hourly.csv',index=False)
    pd.DataFrame({'hour':np.arange(len(holdout)), 'actual_nonpotable_m3':target[split:],'predicted_nonpotable_m3':pred[split:],'meter_with_injected_leak_m3':meter[split:],'anomaly_flag':outliers[split:].astype(int)}).to_csv(OUT/'prediction_and_anomalies.csv',index=False)
    conv_t.to_csv(OUT/'conventional_hourly.csv',index=False)
    smart_t.to_csv(OUT/'smart_hourly.csv',index=False)
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(11,4))
    x=np.arange(168)
    ax.plot(x,target[split:split+168],label='Actual demand',linewidth=1.6)
    ax.plot(x,pred[split:split+168],label='RF forecast',linewidth=1.3,alpha=.85)
    ax.set(xlabel='Hour (first 7 held-out days)',ylabel='Non-potable water demand (m³/h)',title='Out-of-sample demand forecast')
    ax.legend();fig.tight_layout();fig.savefig(OUT/'demand_forecast.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    vals=[holdout.total_water_m3.sum(),holdout.total_water_m3.sum()-conv['reuse_m3'],holdout.total_water_m3.sum()-smart['reuse_m3']]
    bars=ax.bar(['No reuse','Conventional','Predictive'],vals)
    for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+15,f'{v:,.0f} m³',ha='center')
    ax.set(ylabel='30-day municipal intake (m³)',title='Synthetic scenario: municipal water intake');fig.tight_layout();fig.savefig(OUT/'water_comparison.png',dpi=170);plt.close(fig)
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
