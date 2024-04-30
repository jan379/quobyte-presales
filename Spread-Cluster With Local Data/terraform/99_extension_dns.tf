
resource "google_dns_record_set" "root" {
  name         = var.dns_domain
  managed_zone = var.dns_zone
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip]
}


resource "google_dns_record_set" "console" {
  name         = "console.${var.dns_domain}"
  managed_zone = var.dns_zone
  type         = "A"
  ttl          = 300
  rrdatas = google_compute_instance.on-prem.*.network_interface.0.access_config.0.nat_ip
}

resource "google_dns_record_set" "api" {
  name         = "api.${var.dns_domain}"
  managed_zone = var.dns_zone
  type         = "A"
  ttl          = 300
  rrdatas = google_compute_instance.on-prem.*.network_interface.0.access_config.0.nat_ip
}

resource "google_dns_record_set" "s3base" {
  name         = "s3.${var.dns_domain}"
  managed_zone = var.dns_zone
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip]
}

resource "google_dns_record_set" "s3buckets" {
  name         = "*.s3.${var.dns_domain}"
  managed_zone = var.dns_zone
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip]
}

resource "google_dns_record_set" "registry" {
  count        = var.number_on-prem
  name         = "registry${count.index}.${var.dns_domain}"
  managed_zone = var.dns_zone
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem[count.index].network_interface.0.network_ip]
}

resource "google_dns_record_set" "registry-on-prem-srv" {
  name = "_quobyte._tcp.quobyte-demo.com."
  type = "SRV"
  ttl  = 60
  managed_zone = var.dns_zone
  rrdatas = [
    "0 0 7861 ${google_dns_record_set.registry[0].name}",
    "0 0 7861 ${google_dns_record_set.registry[1].name}",
    "0 0 7861 ${google_dns_record_set.registry[2].name}"
  ]
}
