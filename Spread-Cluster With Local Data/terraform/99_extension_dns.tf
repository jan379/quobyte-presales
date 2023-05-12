
resource "google_dns_record_set" "root" {
  name         = google_dns_managed_zone.quobyte.dns_name
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip]
}


resource "google_dns_record_set" "console" {
  name         = "console.${google_dns_managed_zone.quobyte.dns_name}"
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "A"
  ttl          = 300
  rrdatas = google_compute_instance.on-prem.*.network_interface.0.access_config.0.nat_ip
}

resource "google_dns_record_set" "api" {
  name         = "api.${google_dns_managed_zone.quobyte.dns_name}"
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "A"
  ttl          = 300
  rrdatas = google_compute_instance.on-prem.*.network_interface.0.access_config.0.nat_ip
}

resource "google_dns_record_set" "s3base" {
  name         = "s3.${google_dns_managed_zone.quobyte.dns_name}"
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip]
}

resource "google_dns_record_set" "s3buckets" {
  name         = "*.s3.${google_dns_managed_zone.quobyte.dns_name}"
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "A"
  ttl          = 300
  rrdatas = [google_compute_instance.on-prem.0.network_interface.0.access_config.0.nat_ip]
}

resource "google_dns_record_set" "soa" {
  name         = "quobyte-demo.com."
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "SOA"
  ttl          = 21600  
  rrdatas = ["ns-cloud-d1.googledomains.com. cloud-dns-hostmaster.google.com. 1 21600 3600 259200 300"]
}

resource "google_dns_record_set" "ns" {
  name         = "quobyte-demo.com."
  managed_zone = google_dns_managed_zone.quobyte.name
  type         = "NS"
  ttl          = 21600  
  rrdatas = [
    "ns-cloud-d1.googledomains.com.",
    "ns-cloud-c2.googledomains.com.",
    "ns-cloud-b3.googledomains.com.",
    "ns-cloud-a4.googledomains.com."
  ]
}

resource "google_dns_managed_zone" "quobyte" {
  description = "Presales Demo Domain"
  name     = "dynamic-quobyte-demo-new"
  dns_name = "quobyte-demo.com."
  force_destroy = true
}


