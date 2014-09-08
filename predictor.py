
from btb import BTB
from ras import RAS
from bht import BHT
import math

class Predictor:

   def __init__(self, name):
      self.name = name

   def getName(self):
      return self.name

   def predict(self, pc):
      return (False, 0x0)

   def __str__(self):
      return "Predictor (%s)" % self.name

# Model the Rocket front-end, as of 2014 Sept 4 
# Single cycle redirect using the BTB, 
# informed by a gshare BHT and a RAS.
# BTB holds a "is return" bit for RAS popping. 
#
#TODO add sharing the HOB of the PC bits, to allow studying which number of bits to tune to
class RocketPredictor(Predictor):
   
   def __init__(self, w, num_btb_entries, num_ras_entries):
      Predictor.__init__(self, "Rocket")
      self.width = w
      self.btb = BTB(w, int(num_btb_entries),(False,0x0))
      self.ras = RAS(int(num_ras_entries))
      nbht = 2*int(num_btb_entries)
      self.bht = BHT(nbht, int(math.floor(math.log(nbht, 2))))

   def predict(self, pc):
      bht_pred_taken = self.bht.predict(pc)
      (btb_hit, btb_pred) = self.btb.predict(pc)
      (pred_target, pred_is_ret) = btb_pred
      br_offset = 0
      if (pred_is_ret and not self.ras.isEmpty()):
         return (True, self.ras.pop(), br_offset)
      if (bht_pred_taken and btb_hit): 
         return (True, pred_target, br_offset)
      else: 
         return (False, pc+4, br_offset)

   def update(self, commit_bundle, next_pc):
      (pc, taken, target, is_ret, is_call, return_addr) = commit_bundle[0]
      self.btb.update(pc, taken, (target, is_ret))
      self.bht.update(pc, taken)
      if (is_call):
         self.ras.push(return_addr)
      return

