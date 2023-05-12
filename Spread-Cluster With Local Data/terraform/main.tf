// Configure Google Cloud provider
provider "google" {
 credentials = file(var.gcloud_credentials)
 project     = var.gcloud_project 
 region      = var.cluster_region_a 
}


// Region A, on premise
resource "google_compute_instance" "on-prem" {
 count        = var.number_on-prem
 name         = "${var.cluster_name}-server-on-prem${count.index}"
 machine_type = var.flavor_cloud-burst
 zone         = var.cluster_zone_a
 allow_stopping_for_update = true
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = var.image
   }
 }

// fast metadata disk 
 scratch_disk {
  interface = "NVME"
 }

 attached_disk {
  source = google_compute_disk.coreserver-data-a[count.index].name 
 } 

 attached_disk {
  source = google_compute_disk.coreserver-data-b[count.index].name 
 } 

 attached_disk {
  source = google_compute_disk.coreserver-data-c[count.index].name 
 } 

 depends_on = [
  google_compute_disk.coreserver-data-a,
  google_compute_disk.coreserver-data-b,
  google_compute_disk.coreserver-data-c,
 ]


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

// Region B, cloud burst
resource "google_compute_instance" "cloud-burst" {
 count        = var.number_cloud-burst
 name         = "${var.cluster_name}-server-burst${count.index}"
 machine_type = var.flavor_cloud-burst
 zone         = var.cluster_zone_b
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


// some clients on-premise
resource "google_compute_instance" "client-a" {
 count        = var.number_clients_on-prem
 name         = "${var.cluster_name}-client-on-prem${count.index}"
 machine_type = var.flavor_clientserver
 zone         = var.cluster_zone_a
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

// client in region burst
resource "google_compute_instance" "client-b" {
 count        = var.number_clients_burst
 name         = "${var.cluster_name}-client-burst${count.index}"
 machine_type = var.flavor_clientserver
 zone         = var.cluster_zone_b
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

// create necessary disks
resource "google_compute_disk" "coreserver-data-a" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-coredatadisk-${count.index}-a"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem
   zone  = var.cluster_zone_a
}

resource "google_compute_disk" "coreserver-data-b" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-coredatadisk-${count.index}-b"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem
   zone  = var.cluster_zone_a
}

resource "google_compute_disk" "coreserver-data-c" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-coredatadisk-${count.index}-c"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem
   zone  = var.cluster_zone_a
}


// output section
output "bastion-ip" {
 value = google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip
}

