# put k8s into same zone as quobyte cluster to utilize internal networks

# consume storage
```
helm install my-client --set quobyte.registry=frontend.quobyte-demo.com. quobyte/quobyte-client
helm install booli-csi --set quobyte.apiURL=api.quobyte-demo.com --set quobyte.enableAccessKeyMounts=true quobyte/quobyte-csi
```

