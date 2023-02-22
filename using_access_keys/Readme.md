# Using access keys in Quobyte

### Reference
https://support.quobyte.com/docs/16/latest/access_keys.html#access-keys

### For end users
https://support.quobyte.com/docs/16/latest/user_guide.html#access-keys

### Background on access control
https://support.quobyte.com/docs/16/latest/access_control.html


## Scenario 1: Two different users access the same data set

* A database generates some data in K8s.
* A backup user shall access the very same data.

Both share different user identities on different environments.
Database user is running inside a container, not connected to the same user database 
(like LDAP).
Backup user might be running on a traditional liinux machine, identity coming from /etc/passwd | /etc/group

The goal: Both should read and write data using the same identity.

We can do that using access keys. 
This way identity (from a file system perspective) will come from Quobyte user directory.





