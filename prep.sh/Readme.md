# One step Quobyte installer

This script will collect all needed information 
needed to do an Ansible based Quobyte installation.

It will do basic sanity checks:

* Are all hosts reachable via SSH
* Is the installer able to work with root rights.
* Are memory recommendations met
* Are devices available and prepared for an installation.

The expected result will be an Ansible inventory and an 
Ansivle variables declaration describing the cluster.

As a last step the cluster can be installed using Ansible.


