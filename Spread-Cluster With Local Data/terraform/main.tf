// Configure Google Cloud provider
provider "google" {
 credentials = file(var.gcloud_credentials)
 project     = var.gcloud_project 
 region      = var.cluster_region 
}

// on-prem on-prem cluster
resource "google_compute_instance" "on-prem" {
 count        = var.number_on-prem
 name         = "${var.cluster_name}-on-prem${count.index}"
 machine_type = var.flavor_on-prem
 zone         = var.cluster_region
 allow_stopping_for_update = true
 lifecycle {
    ignore_changes = [attached_disk]
 }

 boot_disk {
   initialize_params {
     image = var.image
   }
 }

// stupid cheap HDD
 attached_disk {
  source     = "projects/${var.gcloud_project}/zones/${var.cluster_region}/disks/${var.cluster_name}-disk-${count.index}-a"
 } 

 attached_disk {
  source     = "projects/${var.gcloud_project}/zones/${var.cluster_region}/disks/${var.cluster_name}-disk-${count.index}-b"
 } 

 attached_disk {
  source     = "projects/${var.gcloud_project}/zones/${var.cluster_region}/disks/${var.cluster_name}-disk-${count.index}-c"
 } 

 attached_disk {
  source     = "projects/${var.gcloud_project}/zones/${var.cluster_region}/disks/${var.cluster_name}-disk-${count.index}-d"
 } 

 depends_on = [
  google_compute_disk.disk-a,
  google_compute_disk.disk-b,
  google_compute_disk.disk-c,
  google_compute_disk.disk-d,
 ]

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
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

// cloud extension 
resource "google_compute_instance" "cloud-extension" {
 count        = var.number_cloud-extension
 name         = "${var.cluster_name}-cloud${count.index}"
 machine_type = var.flavor_cloud-extension
 zone         = var.cluster_region
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
  interface = "SCSI"
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
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


// some clients
resource "google_compute_instance" "client" {
 count        = var.number_clientserver
 name         = "${var.cluster_name}-client${count.index}"
 machine_type = var.flavor_clientserver
 zone         = var.cluster_region
 allow_stopping_for_update = true

 boot_disk {
   initialize_params {
     image = var.image 
   }
 }

 metadata = {
   "ssh-keys" = <<EOT
   deploy:${file(var.public_ssh_key)}
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
resource "google_compute_disk" "disk-a" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-disk-${count.index}-a"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem 
   zone  = var.cluster_region
}

resource "google_compute_disk" "disk-b" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-disk-${count.index}-b"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem 
   zone  = var.cluster_region
}

resource "google_compute_disk" "disk-c" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-disk-${count.index}-c"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem 
   zone  = var.cluster_region
}

resource "google_compute_disk" "disk-d" {
   count = var.number_on-prem
   name  = "${var.cluster_name}-disk-${count.index}-d"
   size  = var.disk_size_on-prem
   type  = var.disk_type_on-prem 
   zone  = var.cluster_region
}

// output section
output "bastion-ip" {
 value = google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip
}

