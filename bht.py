
# currenty implements gshare
class BHT:

   def __init__(self, n, hist_sz):
      self.num_entries = n
      self.table = [0]*n
      self.ghistory = 0
      self.ghist_sz = hist_sz          

   def predict(self, pc):
      idx = (pc ^ self.ghistory) % self.num_entries
#      print "pc: 0x%x Table[%d]=%d, Hist=%x, table=%s" % (pc, idx, self.table[idx], self.ghistory, self.table)
      return (self.table[idx] > 1)

   def update(self, pc, taken):
      idx = (pc ^ self.ghistory) % self.num_entries
      old_val = self.table[idx]
      o0 = old_val & 0x1
      o1 = (old_val >> 1) & 0x1
      new_val = ((taken << 1) | (o1 & o0) | ((o1 | o0) & taken))
      self.table[idx] = new_val                      
      self.ghistory = ((self.ghistory << 1) | (int(taken))) & ((1 << self.ghist_sz) -1)
#      print "ghist: %x" % (self.ghistory)


