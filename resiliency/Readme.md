# Quobyte resiliency check

This is pretty agressive: It kills all Quobyte processes (all java processes, 
to be precise) on all machines running a Quobyte metadata service, one machine after the other.
The delay between switching hosts represents the quantified resiliency.


It tries to answer two questions:

* Will the cluster become healthy after tests have ended, or is there 
a way to provoke a state that Quobyte can not recover from?

* How frequent can we kill Quobyte processes without provoking 
I/O errors on the client side

It uses a loop of constantly new created files (covering data + metadata services) to display availability.

To display I/O errors instead of retrying at the client side the policy bubble_errors.sh is appied.


