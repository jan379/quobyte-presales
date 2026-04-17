# Quobyte Cluster Helm Chart, privileged mode

This Helm Chart will install a Quobyte storage cluster.
Containers will run in privileged mode, thus being able 
to use storage devices located on the worker nodes

These storage devices can be used as data- and metadata 
devices for Quobyte.

The registry state can be stored either locally (by providing pre-provisioned 
volumes that match the pvc) or use a standard/ default storage class provided 
by the k8s cluster.

This parameter can be adjusted by using "storageclassRegistry" parameter in values.yaml


