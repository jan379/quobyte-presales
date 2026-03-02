# A widely known storage product

```mermaid
block-beta
columns 1
  db(("Distributed Application workload"))
  blockArrowId6<["&nbsp;&nbsp;&nbsp;"]>(down)
  block:Compute
    Client A
    Client B
    Client C
  end
  space
  D
  Compute  --> D
  Client A --> D
  Client B --> D
  Client C --> D
  style B fill:#969,stroke:#333,stroke-width:4px
```


