# io500 suite as painless as possible

* All nodes need (open)mpi installed
* The io500 binary needs to be compiled, we do that in a central quobyte volume (/quobyte/io500bin) to have it distributed and available on all clients.
* We use two different volumes (io500-data, io500-bin) to separate written data and binary, results, and config.

mpirun --hostfile ~/io500/io500-clients.list /quobyte/io500-bin/io500/io500/io500 /quobyte/io500-bin/io500.ini
