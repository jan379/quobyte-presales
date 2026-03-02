# Architecture diagram


```mermaid
architecture-beta
    group storage(storage)[STORAGE]

    service db(database)[Database] in storage
    service disk1(disk)[Storage] in storage
    service disk2(disk)[Storage] in storage
    service server1(server)[Server] in storage
    service server2(server)[Server] in storage
    service server3(server)[Server] in storage
    service server4(server)[Server] in storage

    db:L -- R:server1
    disk1:T -- B:server1
    disk2:T -- B:db

```







### Resources:
https://mermaid.js.org/syntax/architecture.html
