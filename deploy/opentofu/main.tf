# ---------------------------------------------------------------------------
# Data Boar — OpenTofu module (Docker provider, provider-agnostic)
#
# Usage:
#   tofu init
#   tofu plan
#   tofu apply
#
# After apply, pass the output host/port to Ansible for app configuration:
#   ansible-playbook -i inventory/ deploy/ansible/site.yml
# ---------------------------------------------------------------------------

# Pull the Data Boar image
resource "docker_image" "data_boar" {
  name         = var.data_boar_image
  keep_locally = false
}

# Run the Data Boar container
resource "docker_container" "data_boar" {
  name    = var.container_name
  image   = docker_image.data_boar.image_id
  restart = var.restart_policy

  ports {
    internal = 8088
    external = var.data_boar_port
  }

  # Mount config file (must exist on host before apply)
  volumes {
    host_path      = var.data_boar_config_path
    container_path = "/app/config.yaml"
    read_only      = true
  }

  # Mount report output directory
  volumes {
    host_path      = var.data_boar_output_dir
    container_path = "/app/reports"
    read_only      = false
  }

  healthcheck {
    test         = ["CMD", "curl", "-f", "http://localhost:8088/api/health"]
    interval     = "30s"
    timeout      = "10s"
    retries      = 3
    start_period = "15s"
  }

  labels {
    label = "app"
    value = "data-boar"
  }
}

# ---------------------------------------------------------------------------
# Optional: local PostgreSQL container for POC / testing
# Enable with: tofu apply -var="db_enabled=true" -var="db_password=secret"
# ---------------------------------------------------------------------------

resource "docker_image" "postgres" {
  count        = var.db_enabled ? 1 : 0
  name         = "postgres:16-alpine"
  keep_locally = false
}

resource "docker_container" "postgres" {
  count   = var.db_enabled ? 1 : 0
  name    = "data-boar-poc-db"
  image   = docker_image.postgres[0].image_id
  restart = "unless-stopped"

  ports {
    internal = 5432
    external = 5432
  }

  env = [
    "POSTGRES_DB=poc_scan",
    "POSTGRES_USER=poc_user",
    "POSTGRES_PASSWORD=${var.db_password}",
  ]

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U poc_user -d poc_scan"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# Generate a minimal Ansible inventory pointing at localhost
# (useful when running OpenTofu and Ansible on the same machine)
resource "local_file" "ansible_inventory" {
  content  = <<-INI
    [data_boar]
    localhost ansible_connection=local data_boar_port=${var.data_boar_port}
  INI
  filename = "${path.module}/generated_inventory.ini"
}