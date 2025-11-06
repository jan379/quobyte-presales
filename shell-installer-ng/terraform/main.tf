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
     // sles images require an extra fee, use them only if really necessary
     //image = "projects/suse-cloud/global/images/sles-15-sp7-v20250920-x86-64" 
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

// Seems to be needed for SLES subscriptions to be enabled
 service_account {
        email  = var.serviceaccount_email 
        scopes = [
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/logging.write",
            "https://www.googleapis.com/auth/monitoring.write",
            "https://www.googleapis.com/auth/service.management.readonly",
            "https://www.googleapis.com/auth/servicecontrol",
            "https://www.googleapis.com/auth/trace.append",
        ]
}


 metadata = {
   enable-osconfig = "TRUE"
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

resource "google_compute_instance" "alma_server" {
// alma images are hidden, but can be obtained like this:
// gcloud compute images list --project almalinux-cloud --no-standard-images
 count        = 1
 name         = "alma-machine"
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
     //image = "almalinux-cloud/almalinux-9-v20251014"
     image = "almalinux-cloud/almalinux-9"
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
