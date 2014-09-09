#!/usr/bin/env python

# Assumptions:
#
# We use traces created through the "commit logging" of the Spike RISC-V ISA simulator.
#
# These traces typically only output when exceptions are enabled, meaning there
# are ocassionally "gaps" in the commit log. Also, we "batch" instructions from
# the pipes we get them from, and we don't really handle the edge cases there
# either. It's a SW simulator, were you *expecting* exactly correct behavior?!

# The trace:
#
# [PC]               [instruction] rd [wb-data]
# 0x0000000000002cd4 (0x05070113) x 2 0x0000000000025180
# 0x0000000000002cd8 (0xd8070713) x14 0x0000000000024eb0
# 0x0000000000002cdc (0xea5ff0ef) x 1 0x0000000000002ce0

import optparse
from subprocess import Popen, PIPE
import shlex
from itertools import islice

from btb import BTB
from ras import RAS
from predictor import *


class Stats:
   inst = 0
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
   # jmp/jal (110_1111)
   elif (opcode == 0x6f):
      return 2
   # jalr (110_0111)
   elif (opcode == 0x67):
      return 3
   else:
      return 0

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
   parser.add_option('-f', '--pathtobmarks', dest='bmarkpath',
                    help='Point to the directory (folder) of your benchmarks.', default="../riscv-tools/riscv-tests/benchmarks/")
   parser.add_option('-s', '--benchmark', dest='benchmark',
                    help='RISC-V benchmark to be run in "live" mode.', default="../riscv-tools/riscv-tests/benchmarks/vvadd.riscv")
   parser.add_option('-t', '--tracefile', dest='tracefile',
                    help='input trace file for "replay" mode. Looks inside the trace directory and automatically adds .trace extension.', default="")
   parser.add_option('-p', '--predictor', dest='predictor',
                    help='Choose your predictor.', default="rocket")
   parser.add_option('-w', '--width', dest='width',
                    help='Processor fetch width.', default=1)
   parser.add_option('-b', '--btb-entries', dest='num_btb_entries',
                    help='Number of BTB entries', default=64)
   parser.add_option('-r', '--ras-entries', dest='num_ras_entries',
                    help='Number of RAS entries', default=2)
   (options, args) = parser.parse_args()

#   if options.width != 1:
#      parser.error('Only fetch widths of 1 are supported.')


   if (options.tracefile == ""):
      cmd = "lspike " + options.benchmark
#      cmd = "lspike " + options.bmarkpath + "/" + options.benchmark
      print cmd
      trace = Popen(shlex.split(cmd), stderr=PIPE).stderr
#      parsed_trace = map(ParseLine, trace.readlines())
   else:
      options.benchmark = options.tracefile
      print "opening trace file (traces/%s.trace)" % options.tracefile
      trace = open("traces/" + options.tracefile + ".trace")
#      parsed_trace = map(ParseLine, trace.readlines())

   width = int(options.width)

   if (options.predictor == "rocket"):
      pred = RocketPredictor(width, int(options.num_btb_entries), int(options.num_ras_entries))
   else:
      pred = SSRocketPredictor(width, int(options.num_btb_entries), int(options.num_ras_entries))

   #line_buffer = []
   #line_buffer.append(trace.readline())
   #buff_cnt = 1


#   EndOfFile = False

   
   # 1M gave 33 min bzip (default was 118m)
   block_sz = 10000000
#   line_buffer_generator = islice(trace, block_sz)
#   line_buffer = islice(trace, block_sz)
#   print line_buffer_generator
   
#   for line_buffer in line_buffer_generator:
   while 1:
      line_buffer = islice(trace, block_sz)
      parsed_trace = map(ParseLine, line_buffer)
      t_idx = 0
      trace_sz = len(parsed_trace)
#      print "Size: %d, blk_sz: %d" % (trace_sz, block_sz)

      if (trace_sz < block_sz): break

      while 1:
         # ================================
         # Fetch a bunch of instructions
         # this is similiar backend, not an actual fetch simulated by the processor
         #if (buff_cnt < width + 1):
         #   for i in range(0,2):
         #      line_buffer.append(trace.readline())
         #      buff_cnt += 1

         if (t_idx >= (trace_sz - width - 1)):
            break

         # ================================
         # Perform Fetch & Predict
#      line = line_buffer[0]
#      if not line: break
#      fetch_pc = ParseLineForPC(line)
         (fetch_pc, ignore) = parsed_trace[t_idx]
#      print "i: %d fetch_pc: 0x%x" % (t_idx, fetch_pc)

         #TODO add a predictWithDecodedInst, to experiment with BHT, RAS using decoded instructions
         # use pred_br_offset to "blame" which instruction in the fetch_bundle is the predicted branch
         (pred_taken, pred_target, pred_br_offset) = pred.predict(fetch_pc)

         # ================================
         # Execute Stage

         commit_bundle = []
         was_taken = False          # does the fetch bundle involve a taken br/jmp?
         next_fetch_pc = 0          # where is the next PC going to be if "was_taken"

         br_type = 0
         is_ret = 0

         taken_br_offset = 0

         for i in xrange(0,width):
#         line = line_buffer.pop(0)
#         buff_cnt -= 1
            Stats.inst += 1
#         if not line:
#            EndOfFile = True
#            break
#         (pc, inst) = ParseLine(line)        
            (pc, inst) = parsed_trace[t_idx]
            t_idx += 1

            br_type = isBrOrJmp(inst)
            (is_ret, is_call) = isRetOrCall(br_type, inst)

            if (br_type > 0):
               if (br_type==1): Stats.br += 1
               elif (br_type==2): Stats.jal += 1
               elif (br_type==3): Stats.jalr += 1
               else: print("error")
               if (is_ret): Stats.ret += 1
               elif (is_call): Stats.call += 1

#            next_line = line_buffer[0]
#            if not next_line:
#               EndOfFile = True
#               break
#            target = ParseLineForPC(next_line)
               (target, ignore) = parsed_trace[t_idx] # this is actually "t_idx+1", but we've already incremented it

               if (target != pc+4):
                  Stats.taken += 1
                  was_taken = True
                  taken_br_offset = i

               # Add branch to commit bundle (non-branches are invisible for our purposes)
               next_fetch_pc = target
               ret_addr = pc+4
               commit_bundle.append((pc, was_taken, target, is_ret, is_call, ret_addr))
                           # there can only be one taken branch!
                           # but must give all branches, for the sake of the ghist predictor
                           # in BOOM, BTB is updated in Execute :(,
                           # is each branch allowed to update, or only one update per thing?
                           # sounds like I need to get them a list and let the predictor decide

               if (options.debug):
                  print "pc: 0x%08x, inst: %08x %d, %d target: %x, predtarg: %x (%d), %s%s %s %s" % (pc, inst, isBrOrJmp(inst),
                                                                           was_taken, target, pred_target, pred_target,
                                                                           ("T" if was_taken else "-"),
                                                                           ("RET" if is_ret else "   "),
                                                                           ("CALL" if is_call else "    "),
                                                                           ("PT" if pred_taken else "nT"),
                                                                           )
               # hitting a taken branch means no more valid instructions in this fetch packet
               if (was_taken):
                  break

            else: # !branch
               if (options.debug):
                  print "pc: 0x%08x, inst: %08x %d"  % (pc, inst, isBrOrJmp(inst))

#      if EndOfFile: break


         # =======================================
         # Commit instructions & Update Predictors

         was_mispredicted = False

         # note: next_fetch_pc is only accurate if a br/jmp is taken
         if (pred_taken != was_taken or (was_taken and pred_taken and pred_target != next_fetch_pc)):
            Stats.mispredict += 1
            was_mispredicted = True
            if (is_ret):
               Stats.missed_ret += 1
            if (br_type == 1): Stats.misp_br += 1
            elif (br_type == 2): Stats.misp_jal += 1
            elif (br_type == 3): Stats.misp_jalr += 1

         if (options.debug):
            print "fp: 0x%08x, next_pc: 0x%08x, pred_target: 0x%08x %10s" % (fetch_pc,
                                                                           next_fetch_pc,
                                                                           pred_target,
                                                                           ("MISPREDICT" if was_mispredicted else " "))
            print "----------------------------------"

         if commit_bundle:
            pred.update(fetch_pc, was_taken, next_fetch_pc, commit_bundle, taken_br_offset)



   #---------------------------------------------------


   total = Stats.br + Stats.jal + Stats.jalr
   if (total == 0):
      exit("Huh? Total branch/jmp count is zero!")

   print "\n=============================="
   print "  Stats (%s): " % options.benchmark
   print "   Total insts   : %6d  [%7.3f %% are br/jal/jalr]" % (Stats.inst, 100.*total/Stats.inst)
   print "   Total         : %6d  " % (total)
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
      if (options.benchmark == "median"):    print "Median = 82.5% misp = 330, bj = 1888"
      if (options.benchmark == "multiply"):  print "Multiply = 88.1% mips = 880, bj = 7423"
      if (options.benchmark == "qsort"):     print "qsort = 74.6% mips = 12950 bj = 50908"
      if (options.benchmark == "towers"):    print "Towers = 96.3% mips = 21 bj = 574"
      if (options.benchmark == "dhrystone"): print "dhrystone = 99.8%, misp = 39, bj = 22518"
      if (options.benchmark == "vvadd"):     print "Vvadd = 97.3%, misp = 8, bj= 302, "

   if (options.debug):
      print pred



if __name__ == '__main__':
   main()
