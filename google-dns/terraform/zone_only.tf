resource "google_dns_record_set" "txt-1" {
  name         = "quobyte-demo.com."
  managed_zone = google_dns_managed_zone.quobyte-1.name
  type         = "TXT"
  ttl          = 600  
  rrdatas = [
    "google-site-verification=O11GQamZJ-IZsabVnZtXjApnHTFKxmfnnBjKsZ4h9B0",
  ]
}
resource "google_dns_managed_zone" "quobyte-1" {
  description = "Presales Demo Domain"
  name     = "quobyte-demo-shard-1"
  dns_name = "quobyte-demo.com."
  force_destroy = true
}

resource "google_dns_record_set" "txt-2" {
  name         = "quobyte-demo.com."
  managed_zone = google_dns_managed_zone.quobyte-2.name
  type         = "TXT"
  ttl          = 600  
  rrdatas = [
    "google-site-verification=O11GQamZJ-IZsabVnZtXjApnHTFKxmfnnBjKsZ4h9B0",
  ]
}
resource "google_dns_managed_zone" "quobyte-2" {
  description = "Presales Demo Domain"
  name     = "quobyte-demo-shard-2"
  dns_name = "quobyte-demo.com."
  force_destroy = true
}

resource "google_dns_record_set" "txt-3" {
  name         = "quobyte-demo.com."
  managed_zone = google_dns_managed_zone.quobyte-3.name
  type         = "TXT"
  ttl          = 600  
  rrdatas = [
    "google-site-verification=O11GQamZJ-IZsabVnZtXjApnHTFKxmfnnBjKsZ4h9B0",
  ]
}
resource "google_dns_managed_zone" "quobyte-3" {
  description = "Presales Demo Domain"
  name     = "quobyte-demo-shard-3"
  dns_name = "quobyte-demo.com."
  force_destroy = true
}

resource "google_dns_record_set" "txt-4" {
  name         = "quobyte-demo.com."
  managed_zone = google_dns_managed_zone.quobyte-4.name
  type         = "TXT"
  ttl          = 600  
  rrdatas = [
    "google-site-verification=O11GQamZJ-IZsabVnZtXjApnHTFKxmfnnBjKsZ4h9B0",
  ]
}
resource "google_dns_managed_zone" "quobyte-4" {
  description = "Presales Demo Domain"
  name     = "quobyte-demo-shard-5"
  dns_name = "quobyte-demo.com."
  force_destroy = true
}

