#!/usr/bin/env python

# Assumptions:
#
# We use traces created through the "commit logging" of the Spike RISC-V ISA simulator.
#
# These traces typically only output when exceptions are enabled, meaning there
# are ocassionally "gaps" in the commit log. 

# The trace:
#
# [PC]               [instruction] rd [wb-data]
# 0x0000000000002cd4 (0x05070113) x 2 0x0000000000025180
# 0x0000000000002cd8 (0xd8070713) x14 0x0000000000024eb0
# 0x0000000000002cdc (0xea5ff0ef) x 1 0x0000000000002ce0

import optparse

from btb import BTB
from ras import RAS


# return 0 if not a branch
# non-zero if branch or jmp
def isBrOrJmp(inst):
   opcode = inst & 0x7f
   # branch
   if (opcode == 0x63):
      return 1
   # jmp/jal (1101111)
   elif (opcode == 0x6f):
      return 2
   # jalr (1100111)
   elif (opcode == 0x67):
      return 3
   else:
      return 0

# allow us to look at the next line in the file for matching against the target
def peek_line(f):
   pos = f.tell()
   line = f.readline()
   f.seek(pos)
   return line

def ParseLine(line):
   pc = int(line[2:18], 16)
   inst = int(line[22:30], 16)
   return (pc, inst)

# math for the RAS
def isRetOrFunc(br_type, inst):
   rd = (inst >> 7) & 0x1f
   rs1 = (inst >> 15) & 0x1f #TODO debug that this part is correct
   is_ret = (br_type == 3 and rd == 0 and rs1 == 1)
   is_func = (br_type == 3 and rd == 1)
   return (is_ret, is_func)
      


def main():
   parser = optparse.OptionParser()
   parser.add_option('-d', '--debug', dest='debug',
                    help='Debug mode enabled', default=False)
   parser.add_option('-t', '--tracefile', dest='tracefile',
                    help='input trace file [looks inside the trace directory], automatically adds .trace extension.', default="vvadd")
   parser.add_option('-w', '--width', dest='width',
                    help='Processor fetch width', default=1)
   parser.add_option('-b', '--btb-entries', dest='num_btb_entries',
                    help='Number of BTB entries', default=8)
   parser.add_option('-r', '--ras-entries', dest='num_ras_entries',
                    help='Number of RAS entries', default=8)
   (options, args) = parser.parse_args()

#   if not options.filename:
#      parser.error('Please give an input filename with -f')
   

   trace = open("traces/" + options.tracefile + ".trace")

   width = int(options.width)
   btb = BTB(width,int(options.num_btb_entries))
   ras = RAS(int(options.num_ras_entries))


   stats_br = 0
   stats_jal = 0
   stats_jalr = 0
   stats_taken = 0
   stats_ret = 0
   stats_func = 0
   stats_mispredict = 0


   while 1:
      line = trace.readline()
      if not line: break

      (pc, inst) = ParseLine(line)

      (pred_taken, pred_target) = btb.predict(pc)


      br_type = isBrOrJmp(inst)
      (is_ret, is_func) = isRetOrFunc(br_type, inst)
     
      if (br_type > 0): 
         # TODO "updateStats()"
         if (br_type==1): stats_br += 1
         elif (br_type==2): stats_jal += 1
         elif (br_type==3): stats_jalr += 1
         else: print("error")

         next_line = peek_line(trace)
         (target, n_inst) = ParseLine(next_line)

         was_taken = False 
         was_mispredicted = False

         if (target != pc+4):
            stats_taken += 1
            was_taken = True

         if (pred_taken != was_taken or pred_target != target):
            stats_mispredict += 1
            was_mispredicted = True


         # Update
         btb.update(pc, was_taken, target, pred_taken, pred_target)

         if (options.debug):
            if (was_mispredicted and was_taken):
               print "pc: %08x, inst: %08x %d , target: %x MISPREDICT (%d, %x)" % (pc, inst, isBrOrJmp(inst), target, pred_taken, pred_target)
            elif (was_mispredicted and  not (was_taken)):
               print "pc: %08x, inst: %08x %d , target: %x MISPREDICT (%d, %x) PC+4" % (pc, inst, isBrOrJmp(inst), target, pred_taken, pred_target)
            elif (was_taken):
               print "pc: %08x, inst: %08x %d , target: %x TAKEN" % (pc, inst, isBrOrJmp(inst), target)
            else:
               print "pc: %08x, inst: %08x %d , target: %x PC+4" % (pc, inst, isBrOrJmp(inst), target)
      else:
         if (options.debug):
            print "pc: %08x, inst: %08x %d"  % (pc, inst, isBrOrJmp(inst))


   #---------------------------------------------------

   print "\n=============================="
   print "  Stats (%s): " % options.tracefile
   print "   br            : %6d" % stats_br
   print "   jal           : %6d" % stats_jal
   print "   jalr          : %6d" % stats_jalr
   print ""
   print "  taken          : %6d  [%g %%] " % (stats_taken, 100.*stats_taken/(stats_br+stats_jal+stats_jalr))
   print "  mispredicted   : %6d  [%g %%] " % (stats_mispredict, 100.*stats_mispredict/(stats_br+stats_jal+stats_jalr))
   print "  Accurancy      : %6s  [%g %%] " % ("", 100.-100.*stats_mispredict/(stats_br+stats_jal+stats_jalr))
   print "\n=============================="

   if (options.debug):
      btb.display()

if __name__ == '__main__':
   main()
