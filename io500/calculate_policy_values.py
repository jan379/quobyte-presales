#!/usr/bin/env python3

# number clients
clients = 50

# nie mehr als 178 MPI rank *global*, d.h. über alle clients gerechnet!
max_limit = 178

while(max_limit % clients != 0):
    max_limit -= 1
#print(max_limit)

# Set stripe width to the global upper limit that all processes are 
# allowed to write
stripe_width = max_limit

# minimal number of MPI processes (per node)
# lower limit until integer == TRUE

# number of MPI ranks 
mpi_ranks_per_node = stripe_width / clients

#multiply stripe width by block size
object_size = 47008 * stripe_width
#segment_size = object_size * stripe_width * N  where N in (2,4,8,16...)
segment_size = object_size * stripe_width * 1024

print()
print("Client Count: \t %i" % clients)
print("MPI Ranks: \t %i" % mpi_ranks_per_node)
print("Object Size: \t %i" % object_size)
print("Segment Size: \t %i" % segment_size)
print("Stripe Width: \t %i" % stripe_width)
print()

