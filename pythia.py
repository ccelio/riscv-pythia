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
from predictor import *
 

class Stats:
   br = 0
   jal = 0
   jalr = 0
   taken = 0
   ret = 0
   call = 0
   mispredict = 0
   misp_br = 0
   misp_jal = 0
   misp_jalr = 0
   missed_ret = 0 # how many rets could be predicted if used in the decode stage?
          
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
def isRetOrCall(br_type, inst):
   rd = (inst >> 7) & 0x1f
   rs1 = (inst >> 15) & 0x1f 
   is_ret = (br_type == 3 and rd == 0 and rs1 == 1)
   is_call = ((br_type == 3 or br_type == 2) and rd == 1)
   return (is_ret, is_call)
      


def main():
   parser = optparse.OptionParser()
   parser.add_option('-d', '--debug', action="store_true", dest='debug',
                    help='Debug mode enabled')
   parser.add_option('-t', '--tracefile', dest='tracefile',
                    help='input trace file [looks inside the trace directory], automatically adds .trace extension.', default="vvadd")
   parser.add_option('-p', '--predictor', dest='predictor',
                    help='predictor', default="rocket")
   parser.add_option('-w', '--width', dest='width',
                    help='Processor fetch width', default=1)
   parser.add_option('-b', '--btb-entries', dest='num_btb_entries',
                    help='Number of BTB entries', default=64)
   parser.add_option('-r', '--ras-entries', dest='num_ras_entries',
                    help='Number of RAS entries', default=2)
   (options, args) = parser.parse_args()

#   if not options.filename:
#      parser.error('Please give an input filename with -f')
   

   trace = open("traces/" + options.tracefile + ".trace")

   width = int(options.width)

   if (options.predictor == "rocket"):
      pred = RocketPredictor(width, int(options.num_btb_entries), int(options.num_ras_entries))
   else:
      pred = RocketPredictor(width, int(options.num_btb_entries), int(options.num_ras_entries))


   while 1:
      line = trace.readline()
      if not line: break

      (pc, inst) = ParseLine(line)
      
      #TODO add a predictWithDecodedInst, to experiment with BHT, RAS using decoded instructions
      (pred_taken, pred_target) = pred.predict(pc) 


      br_type = isBrOrJmp(inst)
      (is_ret, is_call) = isRetOrCall(br_type, inst)
     
      if (br_type > 0): 
         # TODO "updateStats()"
         if (br_type==1): Stats.br += 1
         elif (br_type==2): Stats.jal += 1
         elif (br_type==3): Stats.jalr += 1
         else: print("error")

         if (is_ret): Stats.ret += 1
         elif (is_call): Stats.call += 1

         next_line = peek_line(trace)
         (target, n_inst) = ParseLine(next_line)

         was_taken = False 
         was_mispredicted = False

         if (target != pc+4):
            Stats.taken += 1
            was_taken = True

         if (pred_taken != was_taken or (was_taken and pred_taken and pred_target != target)):
            Stats.mispredict += 1
            was_mispredicted = True
            if (is_ret):
               Stats.missed_ret += 1
            if (br_type == 1): Stats.misp_br += 1
            elif (br_type == 2): Stats.misp_jal += 1
            elif (br_type == 3): Stats.misp_jalr += 1


         if (is_ret and was_mispredicted):
            Stats.missed_ret += 1
#         elif (is_ret and pred_taken == was_taken and pred_target == target):
#            print "yah"

         # Update
         ret_addr = pc+4
         pred.update(pc, was_taken, target, pred_taken, pred_target, is_ret, is_call, ret_addr)

         if (options.debug):
            print "pc: 0x%08x, inst: %08x %d, %d target: %x, predtarg: %x (%d), %s %s%s %15s %10s" % (pc, inst, isBrOrJmp(inst), 
                                                                     was_taken, target, pred_target, pred_target,
                                                                     ("T" if was_taken else "-"),
                                                                     ("RET" if is_ret else "   "),
                                                                     ("CALL" if is_call else "    "),
                                                                     ("PT" if pred_taken else "nT"),
                                                                     ("MISPREDICT" if was_mispredicted else " ")
                                                                     )
            #if (was_mispredicted and was_taken):
            #   print "pc: %08x, inst: %08x %d , target: %x MISPREDICT (%d, %x)" % (pc, inst, isBrOrJmp(inst), target, pred_taken, pred_target)
            #elif (was_mispredicted and  not (was_taken)):
            #   print "pc: %08x, inst: %08x %d , target: %x MISPREDICT (%d, %x) PC+4" % (pc, inst, isBrOrJmp(inst), target, pred_taken, pred_target)
            #elif (was_taken):
            #   print "pc: %08x, inst: %08x %d , target: %x TAKEN" % (pc, inst, isBrOrJmp(inst), target)
            #else:
            #   print "pc: %08x, inst: %08x %d , target: %x PC+4" % (pc, inst, isBrOrJmp(inst), target)
      else:
         if (options.debug):
            print "pc: 0x%08x, inst: %08x %d"  % (pc, inst, isBrOrJmp(inst))


   #---------------------------------------------------

   total = Stats.br + Stats.jal + Stats.jalr 

   print "\n=============================="
   print "  Stats (%s): " % options.tracefile
   print "   Total         : %6d   " % (total)
   print "     - br        : %6d  [%7.3f %%] " % (Stats.br  , 100.*Stats.br/total)
   print "     - jal       : %6d  [%7.3f %%] " % (Stats.jal , 100.*Stats.jal/total)
   print "     - jalr      : %6d  [%7.3f %%] " % (Stats.jalr, 100.*Stats.jalr/total)
   print ""
   print "   rets          : %6d  [%7.3f %%] " % (Stats.ret , 100.*Stats.ret/total)
   print "   calls         : %6d  [%7.3f %%] " % (Stats.call, 100.*Stats.call/total)
   print ""
   print "  taken          : %6d  [%7.3f %%] " % (Stats.taken, 100.*Stats.taken/total)
   print "  mispredicted   : %6d  [%7.3f %%] " % (Stats.mispredict, 100.*Stats.mispredict/total)
   print "        - br     : %6d  [%7.3f %%] " % (Stats.misp_br,   100.*Stats.misp_br/  total)
   print "        - br     : %6d  [%7.3f %%] " % (Stats.misp_jal,  100.*Stats.misp_jal/ total)
   print "        - jalr   : %6d  [%7.3f %%] " % (Stats.misp_jalr, 100.*Stats.misp_jalr/total)
   print "     -missed rets: %6d  [%7.3f %%] " % (Stats.missed_ret, 100.*Stats.missed_ret/total)
   print ""
   print "  Accurancy      : %6s  [%7.3f %%] " % ("", 100.-100.*Stats.mispredict/total)
   print "\n=============================="

   # these are the "true" hardware results returned by Rocket.
   # these results only count instructions while "status.ei" is enabled,
   # and is from the uarch counters, which are captured before the branch-heavy
   # printf code is called.
   if (options.predictor == "rocket"):
      if (options.tracefile == "median"):    print "Median = 82.5% misp = 330, bj = 1888"
      if (options.tracefile == "multiply"):  print "Multiply = 88.1% mips = 880, bj = 7423" 
      if (options.tracefile == "qsort"):     print "qsort = 74.6% mips = 12950 bj = 50908"
      if (options.tracefile == "towers"):    print "Towers = 96.3% mips = 21 bj = 574"
      if (options.tracefile == "dhrystone"): print "dhrystone = 99.8%, misp = 39, bj = 22518"
      if (options.tracefile == "vvadd"):     print "Vvadd = 97.3%, misp = 8, bj= 302, "

   if (options.debug):
      print pred

if __name__ == '__main__':
   main()
