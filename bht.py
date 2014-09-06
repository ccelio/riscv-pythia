
# currenty implements gshare
class BHT:

   def __init__(self, n, hist_sz):
      self.num_entries = n
      self.table = [0]*n
      self.ghistory = 0
      self.ghist_sz = hist_sz  
      print "BHT: %d entries, %d history bits" % (self.num_entries, hist_sz)

   def predict(self, pc):
      idx = ((pc >> 2) ^ self.ghistory) % self.num_entries
#      idx = ((pc >> 2)) % self.num_entries
#      print "pc: 0x%8x Table[%d]=%d, Hist=%x, table=%s" % (pc, idx, self.table[idx], self.ghistory, self.table)
#      return ((self.table[idx] & 0x1) == 1)
#      return True
      return (self.table[idx] > 1)

   def update(self, pc, taken):
      idx = ((pc >> 2) ^ self.ghistory) % self.num_entries
#      idx = ((pc >> 2)) % self.num_entries
      val = self.table[idx]
      #o0 = old_val & 0x1 # previous prediction
      #o1 = (old_val >> 1) & 0x1 # previous branch direction
      #new_val = ((taken << 1) | (o1 & o0) | ((o1 | o0) & taken))

      if (taken and not val == 3):
         val += 1
      elif (not taken and not val == 0):
         val -= 1

      self.table[idx] = val
      self.ghistory = ((self.ghistory << 1) | (int(taken))) & ((1 << self.ghist_sz) -1)
#      print "ghist: %x" % (self.ghistory)
#

