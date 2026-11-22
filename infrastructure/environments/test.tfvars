environment = "test"

vpc_cidr = "10.120.0.0/16"

network_http = {
  subnet_name = "test-http"
  cidr        = "10.120.1.0/24"
}

network_db = {
  subnet_name = "test-db"
  cidr        = "10.120.2.0/24"
}

http_instance_names = ["test-http-1"]
db_instance_names   = ["test-db-1"]
