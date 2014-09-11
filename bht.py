
# currenty implements gshare
class BHT:

   def __init__(self, n, hist_sz, shamt = 2):
      self.num_entries = n
      self.table = [0]*n
      self.ghistory = 0
      self.ghist_sz = hist_sz  
      self.shamt = shamt # how many bits to shift off all PC inputs
      print "BHT   : %d entries, %d history bits, %d counter bits" % (self.num_entries, hist_sz, self.num_entries*2)

   def predict(self, pc):
      idx = ((pc >> self.shamt) ^ self.ghistory) % self.num_entries
      return ((self.table[idx] & 0x1) == 1)

   def update(self, pc, taken):
      idx = ((pc >> self.shamt) ^ self.ghistory) % self.num_entries
      val = self.table[idx]
      o0 = val & 0x1 # previous prediction
      o1 = (val >> 1) & 0x1 # previous branch direction
      val = ((taken << 1) | (o1 & o0) | ((o1 | o0) & taken))

      self.table[idx] = val
      self.ghistory = ((self.ghistory << 1) | (int(taken))) & ((1 << self.ghist_sz) -1)
 

