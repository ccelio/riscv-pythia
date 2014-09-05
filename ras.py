
class RAS:

   def __init__(self,n):
      self.num_entries = n
      self.count = 0 
      self.ptr = 0 # point to current item at top of the stack
      self.ras = [0]*n

   def isEmpty(self):
      return (self.count == 0)

   def pop(self):
      if (self.count == 0):
         return 0
      addr = self.ras[self.ptr]
      self.count -= 1
      if (self.ptr == 0):
         self.ptr = self.num_entries-1
      else:
         self.ptr -= 1
      return addr

   def push(self, addr):
      if (self.count != self.num_entries-1):
         self.count += 1
      if (self.ptr == self.num_entries-1):
         self.ptr = 0
      else:
         self.ptr += 1
      self.ras[self.ptr] = addr
  
   def __str__(self):
      return "ras: %d entries, %d count, %d pos, %s\n" % (self.num_entries, self.count, self.ptr, self.ras)

