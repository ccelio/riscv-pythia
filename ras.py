
class RAS:

   ras = []

   def __init__(self,n):
      self.num_entries = n
      self.num_avail = n

   def predict (self, pc):
      if (self.num_avail == self.num_entries):
         return (False, 0)
      (top_pc, target) = self.ras[len(self.ras)-1] #peek
      if (pc == top_pc):
         self.ras.pop()
         self.num_avail += 1
         return (True, target)
      else:
         return (False, target)


   def push(self, pc, target):
      if (self.num_avail > 0):
         self.ras.append((pc, target))
         self.num_avail -= 1

  
   def display(self):
      print "ras: %d entries, %d available" % (self.num_entries, self.num_avail)
      print self.ras
