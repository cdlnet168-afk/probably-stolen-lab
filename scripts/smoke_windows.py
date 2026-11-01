"""Test the actual frozen Windows EXE in a clean directory, never personal data."""
import json, shutil, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

def smoke(exe):
 with tempfile.TemporaryDirectory(prefix='化学发布测试 ') as temp:
  root=Path(temp);app=root/'Probably-Stolen-Lab.exe';shutil.copy2(exe,app)
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  url=f'http://127.0.0.1:{port}'
  def request(path,data=None):
   req=urllib.request.Request(url+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=5) as r:return json.load(r)
  def start():
   proc=subprocess.Popen([str(app),'--no-browser','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   for _ in range(200):
    try:
     if request('/api/health')['version']=='1.0.0':return proc
    except (OSError,ValueError):time.sleep(.05)
   raise AssertionError('EXE did not start')
  def stop(proc):
   subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
   proc.wait(timeout=10)
   for _ in range(100):
    try:request('/api/health');time.sleep(.05)
    except OSError:return
   raise AssertionError('EXE did not stop')
  proc=start()
  try:
   assert (root/'data/lab.sqlite3').is_file()
   assert request('/api/state')['records']==[]
   with urllib.request.urlopen(url+'/') as r:assert 'guide.js' in r.read().decode()
   with urllib.request.urlopen(url+'/recipes.json') as r:assert len(json.load(r))==7
   for rid in ['dream','nightmare','caffeine','phanta','nomore','zyanide','birth']:
    result=request('/api/calculate',dict(kind='plan',recipe=rid,amount=10));assert result['expected_active_ml']>0
   clean=request('/api/calculate',dict(kind='clean',target='fat',amount=10,stock=95,step=1));assert clean['aligned'] and abs(clean['active_ml']-1.25)<1e-9
   request('/api/settings',{'checks':{'smoke':True}})
  finally:stop(proc)
  proc=start()
  try:assert request('/api/state')['settings']['checks']['smoke']
  finally:stop(proc)
  return {'artifact':Path(exe).name,'fresh_database':True,'static_resources':True,'recipes':7,'exact_grid_dilution':True,'restart_persistence':True,'chinese_space_path':True}
if __name__=='__main__':print(json.dumps(smoke(sys.argv[1]),ensure_ascii=False))
