import json, math, socket, subprocess, sys, tempfile, time, unittest, urllib.request, urllib.error
from pathlib import Path
from guide import clean,plan
from engine import finishing
ROOT=Path(__file__).resolve().parent

class ReleaseMathTests(unittest.TestCase):
 def test_grid_conservation(self):
  for target,amount,pct,step in [('fat',10,95,1),('fat',5.2,95,.1),('protein',5.2,95,1),('acid',.37,92,.1)]:
   v=clean(dict(target=target,amount=amount,stock=pct,step=step))
   self.assertTrue(v['aligned'])
   for key in ['prep_stock_ml','prep_water_ml','working_dose_ml']:
    self.assertAlmostEqual(v[key]/step,round(v[key]/step),places=7)
   self.assertAlmostEqual(v['working_dose_ml']*v['prep_pct']/100,v['active_ml'],places=9)
   self.assertAlmostEqual(v['prep_stock_ml']*pct/100,v['prep_total_ml']*v['prep_pct']/100,places=9)
   self.assertGreaterEqual(v['prep_leftover_ml'],-1e-9)
 def test_zero_target(self):self.assertEqual(clean(dict(target='fat',amount=0,stock=95,step=1))['status'],'no_action')
 def test_repack_does_not_double_count(self):self.assertEqual(plan(dict(recipe='zyanide',amount=6,existing=6))['expected_active_ml'],6)
 def test_decimal_portion(self):
  v=finishing(dict(volume=1.8,purity=100,portion=.6,modules=4));self.assertEqual(v['count'],3);self.assertAlmostEqual(v['remainder'],0)
 def test_blocked_keeps_material(self):
  v=finishing(dict(volume=20,purity=98,water=2,portion=5,modules=4));self.assertTrue(v['blocked']);self.assertEqual(v['count'],0);self.assertEqual(v['remainder'],20)
 def test_fractional_module_rejected(self):
  with self.assertRaises(ValueError):finishing(dict(volume=5,purity=100,portion=5,modules=2.5))

class HttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
  cls.base=f'http://127.0.0.1:{cls.port}'
  cls.start()
 @classmethod
 def start(cls):
  cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--no-browser','--port',str(cls.port),'--data-dir',cls.temp.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(100):
   try:
    with urllib.request.urlopen(cls.base+'/api/health',timeout=.2) as r:
     if json.load(r)['version']=='1.0.0':return
   except (OSError,ValueError):time.sleep(.05)
  raise AssertionError('server did not start')
 @classmethod
 def stop(cls):
  cls.proc.terminate();cls.proc.wait(timeout=5)
 @classmethod
 def tearDownClass(cls):cls.stop();cls.temp.cleanup()
 def request(self,path,data=None,headers=None):
  h={'Content-Type':'application/json'};h.update(headers or {})
  req=urllib.request.Request(self.base+path,data=None if data is None else json.dumps(data).encode(),headers=h)
  with urllib.request.urlopen(req,timeout=5) as r:return json.load(r)
 def test_static_and_health(self):
  with urllib.request.urlopen(self.base+'/') as r:self.assertIn('guide.js',r.read().decode())
  self.assertEqual(self.request('/api/health')['app'],'probably-stolen-lab')
 def test_calculate(self):
  v=self.request('/api/calculate',dict(kind='clean',target='fat',amount=10,stock=95,step=1));self.assertTrue(v['aligned']);self.assertAlmostEqual(v['active_ml'],1.25)
 def test_unknown_kind_400(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/calculate',dict(kind='unknown'))
  self.assertEqual(e.exception.code,400);e.exception.close()
 def test_external_origin_rejected(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/settings',{'hello':'world'},{'Origin':'https://example.com'})
  self.assertEqual(e.exception.code,400);e.exception.close()
 def test_persistence_and_backup(self):
  self.request('/api/settings',{'checks':{'test':True}})
  r=self.request('/api/experiment',dict(batch='automated-test',target='fat',reagent='lipobond',version='test',context='isolated',before_total=100,before_pct=10,after_total=100,after_pct=5,dose=1,reagent_pct=95,residual=.325,rounding=.01,temperature=25,usable=True))
  type(self).stop();type(self).start()
  state=self.request('/api/state');self.assertTrue(state['settings']['checks']['test']);self.assertIn(r['id'],[v['id'] for v in state['records']])
  exported=self.request('/api/export');self.assertEqual(exported['schema'],1)
  self.request('/api/import',exported);self.assertEqual(len(self.request('/api/state')['records']),1)
  self.request('/api/delete',{'id':r['id']});self.assertEqual(self.request('/api/state')['records'],[])
  self.assertTrue(list(Path(self.temp.name).glob('before-delete-*.sqlite3')))

if __name__=='__main__':unittest.main()
