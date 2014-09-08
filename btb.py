
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
         return (True, self.btb[pc])
      else:
         return (False, self.default_pkt)

#         print "\nHIT! PC 0x%08x (%d), btb=%s" % (pc, pc, self.btb)
#         print "\n     PC 0x%08x (%d), btb=%s miss... -.-" % (pc, pc, self.btb)

   def update(self, pc, taken, target):
      if (not taken):
         return 
      if pc in self.btb:
         self.btb[pc] = target
         return
      else:
         if (self.num_avail <= 0):
            old_pc = self.history.pop(0) # LRU replacement
            del self.btb[old_pc]
         else:
            self.num_avail -= 1
         self.history.append(pc)
         self.btb[pc] = target
         return
       

   def display(self):
      print "BTB(%d): %d entries" % (self.width, self.num_entries)
      print self.btb
