# Architecture diagram


```mermaid
architecture-beta
    group storage(storage)[STORAGE]

    service db(database)[Database] in storage
    service disk1(disk)[Storage] in storage
    service disk2(disk)[Storage] in storage
    service server(server)[Server] in storage
    service server(server)[Server] in storage
    service server(server)[Server] in storage
    service server(server)[Server] in storage

    db:L -- R:server
    disk1:T -- B:server
    disk2:T -- B:db

```







### Resources:
https://mermaid.js.org/syntax/architecture.html
