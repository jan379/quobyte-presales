// Configure Google Cloud provider
provider "google" {
 credentials = file(var.gcloud_credentials)
 project     = var.gcloud_project 
 region      = var.cluster_region 
}

// List available zones in chosen region
data "google_compute_zones" "available" {
  region = var.cluster_region
}

locals {
  cluster_zone = data.google_compute_zones.available.names[0]
}

// test all flavors
resource "google_compute_instance" "debian_server" {
 count        = 1
 name         = "deb-machine"
 machine_type = "n1-standard-8" 
 zone         = local.cluster_zone
 allow_stopping_for_update = true
 scheduling { 
   provisioning_model = "SPOT"
   preemptible = true
   automatic_restart = false
 }
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = "debian-cloud/debian-12" 
   }
 }

// one metadata device 
 scratch_disk {
  interface = "NVME"
 }

// one fast data devices 
 scratch_disk {
  interface = "NVME"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
EOT
 }

 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}

resource "google_compute_instance" "rocky_server" {
 count        = 1
 name         = "rocky-machine"
 machine_type = "n1-standard-8" 
 zone         = local.cluster_zone
 allow_stopping_for_update = true
 scheduling { 
   provisioning_model = "SPOT"
   preemptible = true
   automatic_restart = false
 }
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = "rocky-linux-cloud/rocky-linux-9-optimized-gcp" 
   }
 }

// one metadata device 
 scratch_disk {
  interface = "NVME"
 }

// one fast data devices 
 scratch_disk {
  interface = "NVME"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
EOT
 }

 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}

resource "google_compute_instance" "suse_server" {
 count        = 1
 name         = "suse-machine"
 machine_type = "n1-standard-8" 
 zone         = local.cluster_zone
 allow_stopping_for_update = true
 scheduling { 
   provisioning_model = "SPOT"
   preemptible = true
   automatic_restart = false
 }
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = "opensuse-cloud/opensuse-leap" 
   }
 }

// one metadata device 
 scratch_disk {
  interface = "NVME"
 }

// one fast data devices 
 scratch_disk {
  interface = "NVME"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
EOT
 }

 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}

resource "google_compute_instance" "ubuntu_server" {
 count        = 1
 name         = "ubuntu-machine"
 machine_type = "n1-standard-8" 
 zone         = local.cluster_zone
 allow_stopping_for_update = true
 scheduling { 
   provisioning_model = "SPOT"
   preemptible = true
   automatic_restart = false
 }
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64" 
   }
 }

// one metadata device 
 scratch_disk {
  interface = "NVME"
 }

// one fast data devices 
 scratch_disk {
  interface = "NVME"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
EOT
 }

 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}


// output section
output "bastion-ip" {
 value = google_compute_instance.debian_server.0.network_interface.0.access_config.0.nat_ip
}
