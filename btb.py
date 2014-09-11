from collections import OrderedDict

class BTB:

   def __init__(self,w,n,default):
      self.btb = OrderedDict()
      self.width = w
      self.num_entries = n
      self.default_pkt = default

   def predict(self, pc):
      if pc in self.btb:
         return (True, self.btb[pc])
      else:
         return (False, self.default_pkt)

   def update(self, pc, taken, target):
      if (not taken):
         return 
      self.btb[pc] = target
      if len(self.btb) > self.num_entries:
         self.btb.popitem(last=False)

   def display(self):
      print "BTB(%d): %d entries" % (self.width, self.num_entries)
      print self.btb

