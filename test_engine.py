import unittest
from engine import *
class MathTests(unittest.TestCase):
 def test_dilution(self):
  v=dilution(dict(stock=95,target=10,diluent=0,volume=10));self.assertAlmostEqual(v['stock_ml'],1/0.95);self.assertAlmostEqual(v['active_ml'],1)
 def test_existing_stock(self):
  v=dilution(dict(stock=95,target=5,diluent=0,volume=1,mode='stock'));self.assertAlmostEqual(v['final_ml'],19)
 def test_bad_target(self):
  with self.assertRaises(ValueError):dilution(dict(stock=5,target=95,diluent=0,volume=1))
 def test_mixing(self):
  v=mixing({'rows':[dict(volume=1,components={'base':95,'water':5}),dict(volume=9,components={'water':100})]});self.assertAlmostEqual(v['components'][0]['percent'],9.5)
 def record(self):
  return dict(target='fat',reagent='lipo',version='1',context='26C',before_total=100,before_pct=5.2,dose=2,reagent_pct=50,after_total=100,after_pct=4.2,residual=0,completed=True,rounding=.01)
 def test_pure_dilution_not_reaction(self):
  r=self.record();r.update(after_total=200,after_pct=2.6)
  validate_experiment(r)
  self.assertEqual(predict(dict(target='fat',reagent='lipo',version='1',context='26C',amount=1,concentration=100),[r])['status'],'insufficient')
 def test_predict_concentration(self):
  r=self.record();v=predict(dict(target='fat',reagent='lipo',version='1',context='26C',amount=5.2,concentration=95,step=.1),[r]);self.assertAlmostEqual(v['dose_ml'],5.2/.95);self.assertEqual(v['rounded_ml'],5.5)
 def test_conditions_never_mix(self):
  v=predict(dict(target='fat',reagent='lipo',version='2',context='26C',amount=5.2,concentration=95),[self.record()]);self.assertEqual(v['status'],'insufficient')
 def test_overdose_endpoint_is_bound(self):
  r=self.record();r.update(after_pct=0,residual='');v=predict(dict(target='fat',reagent='lipo',version='1',context='26C',amount=5.2,concentration=95),[r]);self.assertEqual(v['status'],'insufficient');self.assertIsNotNone(v['upper_ratio'])
 def test_finisher_blocks_water(self):
  v=finishing(dict(volume=20,purity=99,water=1,modules=0,portion=5));self.assertTrue(v['blocked']);self.assertAlmostEqual(v['active_percent'],87.12)
 def test_nonfinite(self):
  with self.assertRaises(ValueError):num('nan','x')
if __name__=='__main__':unittest.main()
