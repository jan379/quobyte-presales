// Configure Google Cloud provider
provider "google" {
 credentials = file(var.gcloud_credentials)
 project     = var.gcloud_project 
 region      = var.cluster_region_a 
}

// Region One
resource "google_compute_instance" "on-prem" {
 count        = var.number_on-prem
 name         = "${var.cluster_name}-on-prem${count.index}"
 machine_type = var.flavor_cloud-extension
 zone         = var.cluster_region_a
 allow_stopping_for_update = true
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = var.image
   }
 }
// fast nvme storage tier
 scratch_disk {
  interface = "NVME"
 }
 scratch_disk {
  interface = "NVME"
 }
 scratch_disk {
  interface = "NVME"
 }
// fast metadata disk 
 scratch_disk {
  interface = "NVME"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
   deploy:${file(var.public_ssh_key-support)}
EOT
 }

 // install necessary software
 metadata_startup_script = local.startupscript_on-prem_debflavor
 
 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}

// Region Two
resource "google_compute_instance" "cloud-extension" {
 count        = var.number_cloud-extension
 name         = "${var.cluster_name}-cloud${count.index}"
 machine_type = var.flavor_cloud-extension
 zone         = var.cluster_region_b
 allow_stopping_for_update = true
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = var.image
   }
 }

// fast nvme storage tier
 scratch_disk {
  interface = "NVME"
 }
 scratch_disk {
  interface = "NVME"
 }
 scratch_disk {
  interface = "NVME"
 }
// fast metadata disk 
 scratch_disk {
  interface = "NVME"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
   deploy:${file(var.public_ssh_key-support)}
EOT
 }

 // install necessary software
 metadata_startup_script = local.startupscript_on-prem_debflavor

 network_interface {
   network = "default"

   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}


// some clients in region A
resource "google_compute_instance" "client-a" {
 count        = var.number_clientserver
 name         = "${var.cluster_name}-client-a${count.index}"
 machine_type = var.flavor_clientserver
 zone         = var.cluster_region_a
 allow_stopping_for_update = true

 boot_disk {
   initialize_params {
     image = var.image 
   }
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
   deploy:${file(var.public_ssh_key-support)}
EOT
 }

// install needed software 
 metadata_startup_script = local.startupscript_on-prem_debflavor

 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}

// client in region B
resource "google_compute_instance" "client-b" {
 //count        = var.number_clientserver
 count        = 1
 name         = "${var.cluster_name}-client-b"
 machine_type = var.flavor_clientserver
 zone         = var.cluster_region_b
 allow_stopping_for_update = true

 boot_disk {
   initialize_params {
     image = var.image 
   }
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
   deploy:${file(var.public_ssh_key-support)}
EOT
 }

// install needed software 
 metadata_startup_script = local.startupscript_on-prem_debflavor

 network_interface {
   network = "default"
   access_config {
     // Include this section to give the VM an external ip address
   }
 }
}


// output section
output "bastion-ip" {
 value = google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip
}

