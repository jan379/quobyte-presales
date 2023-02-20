### A quickstart script 
resource "local_file" "quickstart" {
 content = templatefile("templates/quickstart.sh",
 {
  registry_ips = join(",", google_compute_instance.on-prem.*.network_interface.0.network_ip) 
  api_ip = google_compute_instance.on-prem.0.network_interface.0.network_ip 
  cluster_name = var.cluster_name 
  net_cidr = var.net_cidr 
 }
 )
 filename = "quickstart.sh"
 file_permission = "0750"
 provisioner "local-exec" {
   command = "until scp templates/quickstart.sh deploy@${google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip}: ; do sleep 1; done"
 }
}
