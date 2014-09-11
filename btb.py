from collections import OrderedDict

class BTB:

   def __init__(self,w,n,default):
      self.btb = OrderedDict()
      self.width = w
      self.num_entries = n
      self.default_pkt = default
      print "BTB   : %d entries" % self.num_entries

   def predict(self, pc):
#      print (("pred pc: 0x%x : " % pc) + self.__str__())
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

   def __str__(self):
      string = "("
      for pc in self.btb:
         string += ("(0x%x,0x%x.." % (pc, self.btb[pc][0]))
      string += ")"
      return string



