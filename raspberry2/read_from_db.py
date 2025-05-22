import requests
from requests.auth import HTTPBasicAuth

INFLUXDB_URL = "http://10.64.44.156:8086" # Public IP: 194.177.207.38
ADMIN_USER = "username"
ADMIN_PASS = "password"

def create_user(username, password):
  query = f"CREATE USER {username} WITH PASSWORD '{password}'"
  response = requests.get(f"{INFLUXDB_URL}/query", params={"q": query}, auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASS))
  print("Create user:", response.text)

def create_database(db_name):
  query = f"CREATE DATABASE {db_name}"
  response = requests.get(f"{INFLUXDB_URL}/query", params={"q": query}, auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASS))
  print("Create database:", response.text)

def grant_privileges(username, db_name):
  query = f"GRANT ALL ON {db_name} TO {username}"
  response = requests.get(f"{INFLUXDB_URL}/query", params={"q": query}, auth=HTTPBasicAuth(ADMIN_USER, ADMIN_PASS))
  print("Grant privileges:", response.text)

def insert_data(db_name, user, password, measurement, value, timestamp=None):
  line = f"{measurement} value={value}"
  if timestamp:
    line += f" {timestamp}"
  response = requests.post(f"{INFLUXDB_URL}/write", 
                            params={"db": db_name},
                            data=line,
                            auth=HTTPBasicAuth(user, password))
  print("Insert data:", response.ok)

def query_data(db_name, user, password, measurement):
  query = f"SELECT * FROM {measurement}"
  response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
  print("Query result:", response.text)

def delete_data(db_name, user, password, condition="time < now()"):
  query = f"DELETE FROM air_temperature WHERE {condition}"
  response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
  print("Delete data:", response.text)

student_user = "team19"
student_pass = "team19(@#$"
db_name = "team19_db"
measurement = "air_temperature"

# create_user(student_user, student_pass)
# create_database(db_name)
# grant_privileges(student_user, db_name)

insert_data(db_name, student_user, student_pass, measurement, 25.5)
query_data(db_name, student_user, student_pass, measurement)
# insert_data(db_name, student_user, student_pass, measurement, 24.0, timestamp="1746614535228053223")  # Optional timestamp
# delete_data(db_name, student_user, student_pass)
