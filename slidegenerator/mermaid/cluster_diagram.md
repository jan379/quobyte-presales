# A widely known storage product

```mermaid
block
columns 1
  block:Compute
  columns 10
    C1["Client A"]
    C2["Client B"]
    C3["Client C"]
    C4["Client D"]
    C5["Client E"]
    C5["Client F"]
  end
  block:Storage
    block:S1
    columns 1
      label1["Server 1"]:1
      disk1[("disk 01")]
      disk2[("disk 02")]
      disk3[("disk 03")]
      disk4[("disk 04")]
    end
    block:S2(" ")
    columns 1
      label2["Server 2"]:1
      disk5[("disk 05")]
      disk6[("disk 06")]
      disk7[("disk 07")]
      disk8[("disk 08")]
    end
    block:S3(" ")
    columns 1
      label3["Server 3"]:1
      disk9[("disk 09")]
      disk10[("disk 10")]
      disk11[("disk 11")]
      disk12[("disk 12")]
    end
    block:S4(" ")
    columns 1
      label4["Server 4"]:1
      disk13[("disk 13")]
      disk14[("disk 14")]
      disk15[("disk 15")]
      disk16[("disk 16")]
    end
  end
  C1 --> disk3
  C1 --> disk7
  C1 --> disk14
  C2 --> disk2
  C2 --> disk5
  C2 --> disk12
  C3 --> disk1
  C3 --> disk6 
  C3 --> disk13
  C4 --> disk4
  C4 --> disk10
  C4 --> disk16
  C5 --> disk8
  C5 --> disk9
  C5 --> disk15
classDef server fill:white,stroke:blue,stroke-width:4px;
classDef client fill:#966,stroke:#333;
classDef label fill:white,stroke:white;

class S1,S2,S3,S4 server
class label1,label2,label3,label4 label

```


