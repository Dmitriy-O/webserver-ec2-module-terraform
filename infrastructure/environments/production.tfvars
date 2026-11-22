environment = "production"

vpc_cidr = "10.121.0.0/16"

network_http = {
  subnet_name = "production-http"
  cidr        = "10.121.1.0/24"
}

network_db = {
  subnet_name = "production-db"
  cidr        = "10.121.2.0/24"
}

http_instance_names = ["production-http-1"]
db_instance_names   = ["production-db-1"]
