import unittest
from guide import plan,clean
from engine import finishing
class GuideTests(unittest.TestCase):
 def test_effective_not_bottle(self):
  v=plan(dict(recipe='dream',amount=10,alcohol_pct=70));self.assertAlmostEqual(v['additions'][0]['stock_ml'],50/.7);self.assertEqual(v['expected_active_ml'],5)
 def test_coffee_existing(self):
  v=plan(dict(recipe='caffeine',amount=20,existing=2,solvent=5));self.assertEqual(v['additions'][0]['active_ml'],15);self.assertEqual(v['expected_active_ml'],17)
 def test_phanta(self):
  v=plan(dict(recipe='phanta',amount=100,reducer_pct=50));self.assertEqual(v['additions'][0]['stock_ml'],150);self.assertEqual(v['expected_active_ml'],10)
 def test_nomore_catalyst(self):
  v=plan(dict(recipe='nomore',amount=40));self.assertEqual([x['active_ml'] for x in v['additions']],[40,10]);self.assertEqual(v['expected_active_ml'],24)
 def test_fat_orientation(self):
  v=clean(dict(target='fat',amount=19.2,stock=95));self.assertAlmostEqual(v['active_ml'],2.4);self.assertAlmostEqual(v['stock_ml']*.95,2.4);self.assertAlmostEqual(v['dose_ml']*v['working_pct']/100,2.4)
 def test_no_stabilizer_ratio(self):
  with self.assertRaises(ValueError):clean(dict(target='stabilizer',amount=10))
 def test_combined_dry_threshold(self):
  d=dict(volume=10,purity=98,water=.5,alcohol=.5,lipobond=0,portion=2,modules=4)
  self.assertFalse(finishing(d)['blocked']);d['lipobond']=.01;self.assertTrue(finishing(d)['blocked'])
 def test_mod_limit(self):
  self.assertEqual(plan(dict(recipe='dream',amount=10,modules=2))['max_percent'],97)
if __name__=='__main__':unittest.main()
