*Christopher Celio*
2014 Sep 1

This is a trace-based simulator designed to explore branch prediction
strategies. 

In particular, BTB, BHT, and RAS interations with superscalar fetch units.

Getting Started
---------------

*replay mode*

    ./pythia -t vvadd

*live mode*
    
    ./pythia -s ../riscv-tools/riscv-tests/benchmarks/vvadd.riscv

Live mode assumes "lspike" is installed.

For more information:

    ./pythia -h


There are *two* modes - "live" mode and "replay" mode.


*"Live" mode* - is the default mode that invokes "lspike" and pipes the commit
log to Pythia. use "-s" to specify the benchmark and its arguments. 

*"Replay" mode* - use "-t" to name a tracefile in the "traces" directory to replay a run.

Setting Up
----------

"Live" mode will require the [riscv-tools](https://github.com/ucb-bar/riscv-tools) 
to be installed. In particular, it needs to make use of the "commit logging"
ability of "spike".

1. Modify riscv-tool's "build.sh" to compile the "spike" ISA simulator into a new directory.

```
build_project riscv-fesvr --prefix=$RISCV/logger
build_project riscv-isa-sim --prefix=$RISCV/logger --with-fesvr=$RISCV/logger --enable-commitlog 
```

2. Rename $RISCV/logger/bin/spike to $RISCV/logger/bin/lspike. 

3. Finally, add $RISCV/logger/bin to your bash environment path. 

