
class BTB:

   btb = {}
   history = []
                    
   def __init__(self,w,n,default):
      self.width = w
      self.num_entries = n
      self.num_avail = n
      self.default_pkt = default

   def predict(self, pc):
      if pc in self.btb:
#         print "\nHIT! PC 0x%08x (%d), btb=%s" % (pc, pc, self.btb)
         return (True, self.btb[pc])
      else:
#         print "\n     PC 0x%08x (%d), btb=%s miss... -.-" % (pc, pc, self.btb)
         return (False, self.default_pkt)

   # TODO needs to delete an entry on a not-taken branch?
   def update(self, pc, taken, target, pred_taken, pred_target):
      if (not taken):
         return 
      if pc in self.btb:
         self.btb[pc] = target
         return
      else:
         if (self.num_avail <= 0):
            # TODO delete a random entry? or is this LRU? 
            old_pc = self.history.pop(0)
#            del self.btb[old_pc]
         else:
            self.num_avail -= 1
         self.history.append(pc)
         self.btb[pc] = target
         return
       

   def display(self):
      print "BTB(%d): %d entries" % (self.width, self.num_entries)
      print self.btb
