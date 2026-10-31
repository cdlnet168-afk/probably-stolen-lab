import unittest
from engine import neutralization
class NeutralizationTests(unittest.TestCase):
 def setup_data(self):
  return dict(input_unit='ml',current=5.2,remaining=0,stock=95,working=10,prepare_mode='concentration',ratio_mode='manual',ratio=2,ratio_source='fictional test only',step=.1)
 def test_diluted_stock(self):
  v=neutralization(self.setup_data(),[]);self.assertAlmostEqual(v['dose_ml'],104);self.assertAlmostEqual(v['stock_ml'],10.4/.95);self.assertAlmostEqual(v['water_ml'],104-10.4/.95)
 def test_percent_and_remaining(self):
  d=self.setup_data();d.update(input_unit='percent',current=5.2,solution_volume=200,remaining=.4)
  v=neutralization(d,[]);self.assertAlmostEqual(v['remove_ml'],10)
 def test_dose_reverse(self):
  d=self.setup_data();d.update(prepare_mode='dose',desired_dose=20)
  v=neutralization(d,[]);self.assertAlmostEqual(v['working'],52)
 def test_unreachable_concentration(self):
  d=self.setup_data();d.update(prepare_mode='dose',desired_dose=1)
  with self.assertRaises(ValueError):neutralization(d,[])
 def test_no_ratio_no_guess(self):
  d=self.setup_data();d.update(ratio_mode='database',target='protein',reagent='acid',version='v',context='x')
  self.assertEqual(neutralization(d,[])['status'],'insufficient')
 def test_batch_keeps_leftover(self):
  d=self.setup_data();d.update(batch=200)
  v=neutralization(d,[]);self.assertAlmostEqual(v['leftover_ml'],96)
 def test_already_zero(self):
  d=self.setup_data();d['current']=0
  self.assertEqual(neutralization(d,[])['status'],'no_action')
 def test_manual_source_required(self):
  d=self.setup_data();d['ratio_source']=''
  with self.assertRaises(ValueError):neutralization(d,[])
if __name__=='__main__':unittest.main()
