
from btb import BTB
from ras import RAS

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
class RocketPredictor(Predictor):
   
   def __init__(self, w, num_btb_entries, num_ras_entries):
      Predictor.__init__(self, "Rocket")
      self.width = w
      self.btb = BTB(w, int(num_btb_entries),(False,0x0))
      self.ras = RAS(int(num_ras_entries))

   def predict(self, pc):
      (pred_taken, btb_pred) = self.btb.predict(pc)
      (pred_target, pred_is_ret) = btb_pred
#      if (pred_is_ret and not self.ras.isEmpty()):
#         print self.ras
#         return (True, self.ras.pop())
#      else: 
#         return (pred_taken, pred_target)
      return (pred_taken, pred_target)


   def update(self, pc, taken, target, pred_taken, pred_target, is_ret, is_call, return_addr):
      self.btb.update(pc, taken, (target, is_ret), pred_taken, pred_target)
      if (is_call):
#         print self.ras
         self.ras.push(return_addr)
#         print self.ras
      return

