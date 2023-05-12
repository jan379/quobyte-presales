// Within this file all variables are defined to adjust 
// Quobyte cluster settings.

variable "net_cidr" {
  type = string
  default = "10.0.0.0/8"
}

// configure cluster scope variables
variable "cluster_name" {
  type = string
  default = "image-store"
}

variable "git_repository" {
  type = string
  default = "https://github.com/quobyte/quobyte-ansible.git"
}

variable "image" {
  type = string
  default = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "number_on-prem" {
  type = number
  default = 5
}

variable "number_cloud-extension" {
  type = number
  default = 1
}

variable "disk_type_on-prem" {
  type = string
  default = "pd-standard"
}

variable "disk_size_on-prem" {
  type = number
  default = 500
}


variable "flavor_on-prem" {
  type = string
  default = "e2-standard-4"
}

variable "flavor_cloud-extension" {
  type = string
  default = "n1-standard-8"
}

variable "number_clientserver" {
  type = number
  default = 10 
}

variable "flavor_clientserver" {
  type = string
  default = "e2-standard-4"
}

locals {
  startupscript_on-prem_debflavor = "curl https://raw.githubusercontent.com/jan379/quobyte-presales/master/Spread-Cluster%20With%20Local%20Data/terraform/quickstart.sh > /home/deploy/quickstart.sh; chown deploy: /home/deploy/quickstart.sh; chmod 755 /home/deploy/quickstart.sh"
}


