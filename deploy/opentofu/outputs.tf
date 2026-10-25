output "data_boar_url" {
  description = "URL to reach the Data Boar web interface."
  value       = "http://localhost:${var.data_boar_port}"
}

output "data_boar_port" {
  description = "Host port the Data Boar container is bound to."
  value       = var.data_boar_port
}

output "container_name" {
  description = "Name of the running Data Boar Docker container."
  value       = docker_container.data_boar.name
}

output "ansible_inventory_path" {
  description = "Path to the generated Ansible inventory file."
  value       = local_file.ansible_inventory.filename
}

output "poc_db_host" {
  description = "PostgreSQL host for POC database (empty when db_enabled = false)."
  value       = var.db_enabled ? "localhost" : ""
}

output "poc_db_port" {
  description = "PostgreSQL port for POC database."
  value       = var.db_enabled ? 5432 : null
}