### The Ansible inventory file
resource "local_file" "AnsibleInventory" {
 content = templatefile("templates/inventory.tmpl",
 {
  on-prem_ip = join(":\n      ", google_compute_instance.on-prem.*.network_interface.0.network_ip) 
  on-prem_ips = google_compute_instance.on-prem.*.network_interface.0.network_ip 
  cloud-extension_ip = join(":\n      ", google_compute_instance.cloud-extension.*.network_interface.0.network_ip)
  client_ip = join(":\n      ", google_compute_instance.client-a.*.network_interface.0.network_ip, google_compute_instance.client-b.*.network_interface.0.network_ip)
 }
 )
 filename = "provisioning/ansible-inventory.yaml"
 file_permission = "0644"
 provisioner "local-exec" {
   command = "until scp provisioning/ansible-inventory.yaml deploy@${google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip}: ; do sleep 1 ; done"
 }
}
