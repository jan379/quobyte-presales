// Within this file all variables are defined to adjust 
// Quobyte cluster settings.

variable "net_cidr" {
  type = string
  default = "10.0.0.0/8"
}

// configure cluster scope variables
variable "cluster_name" {
  type = string
  default = "qb-multizone"
}

variable "git_repository" {
  type = string
  default = "https://github.com/quobyte/quobyte-ansible.git"
}

variable "cluster_region_a" {
  type = string
  default = "europe-west4"
}

variable "cluster_region_b" {
  type = string
  default = "europe-west4"
}

variable "cluster_zone_a" {
  type = string
  default = "europe-west4-a"
}

variable "cluster_zone_b" {
  type = string
  default = "europe-west4-b"
}

variable "image" {
  type = string
  default = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "number_on-prem" {
  type = number
  default = 3
}

variable "number_cloud-burst" {
  type = number
  default = 3
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

variable "flavor_cloud-burst" {
  type = string
  default = "n1-standard-8"
}

variable "number_clients_burst" {
  type = number
  default = 1 
}

variable "number_clients_on-prem" {
  type = number
  default = 1 
}

variable "flavor_clientserver" {
  type = string
  default = "e2-standard-4"
}

locals {
  startupscript_on-prem_debflavor = "curl https://raw.githubusercontent.com/jan379/quobyte-presales/master/Spread-Cluster%20With%20Local%20Data/terraform/quickstart.sh > /home/deploy/quickstart.sh; chown deploy: /home/deploy/quickstart.sh; chmod 755 /home/deploy/quickstart.sh"
}


