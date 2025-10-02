resource "google_compute_firewall" "webconsole-rules" {
  project     = var.gcloud_project 
  name        = "quobyte-webconsole-firewall"
  network     = "default"
  description = "Open TCP ports used by Quoybyte webconsole and S3"

  allow {
    protocol  = "tcp"
    ports     = ["8080", "80"]
  }

  source_ranges = ["0.0.0.0/0"]
}
