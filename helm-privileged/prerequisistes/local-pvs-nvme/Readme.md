# Prerequisites for local storage Quobyte

In order to work with Quobyte cluster Helm charts
your storage devices needs to be abstracted as Persistent Volumes.

Quobyte will use these persistent volumes to store any date it requires.

There are three stateful components in Quobyte:

# Registry data

Registry state stores the Quobyte cluster state. It does not require
much space, one persitent volume with 30Gi should be enough

# Metadata

Metadata state stores any file metadata, it will grow with numbers of files
sotred in Quobyte. It should reside on fast storage media, one 1Ti PV should be
enough for most workloads.

# File data

Data state can be stored on many PVs/ devices with different storage media types.
Plan it according to your capacity needs. One data PV with at least 300Gi is the
required minimum.

You can create pv declarations this way:

```bash
kubectl get nodes| awk '{print $1}' | grep -v ^NAME | while read line; do sed s/NODENAME/$line/g registry_pv_template.yaml > ${line}_rpv.yaml; done
```
