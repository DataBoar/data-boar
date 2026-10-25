variable "data_boar_image" {
  description = "Data Boar Docker image to deploy."
  type        = string
  default     = "fabioleitao/data-boar:latest"
}

variable "data_boar_port" {
  description = "Host port to expose the Data Boar web interface on."
  type        = number
  default     = 8088
}

variable "data_boar_config_path" {
  description = "Absolute path to the Data Boar config file on the host."
  type        = string
  default     = "/etc/data-boar/config.yaml"
}

variable "data_boar_output_dir" {
  description = "Absolute path to the report output directory on the host."
  type        = string
  default     = "/var/data-boar/reports"
}

variable "container_name" {
  description = "Name for the Data Boar Docker container."
  type        = string
  default     = "data-boar"
}

variable "restart_policy" {
  description = "Docker restart policy (no, on-failure, always, unless-stopped)."
  type        = string
  default     = "unless-stopped"
}

variable "db_enabled" {
  description = "If true, also provision a local PostgreSQL container for POC/testing."
  type        = bool
  default     = false
}

variable "db_password" {
  description = "Password for the POC PostgreSQL database. Only used when db_enabled = true."
  type        = string
  sensitive   = true
  default     = ""
}