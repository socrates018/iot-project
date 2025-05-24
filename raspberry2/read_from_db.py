import requests
from requests.auth import HTTPBasicAuth
import getpass

INFLUXDB_URL = "http://194.177.207.38:8086"  # Private IP: 10.64.44.156:8086
ADMIN_USER = "username"
ADMIN_PASS = "password"  # No longer hardcoded

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
  return response

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

# Query all data
response = query_data(db_name, student_user, student_pass, measurement)

# Check if data exists and print confirmation
try:
    data = response.json()
    results = data.get("results", [])
    if results and "series" in results[0]:
        print("✅ Data found in the database.")
        # Save all data to a local file
        with open("exported_data.txt", "w", encoding="utf-8") as f:
            import json
            json.dump(results[0]["series"], f, indent=2)
        print("📁 All data exported to 'exported_data.txt'.")
    else:
        print("⚠️ No data found in the database.")
except Exception as e:
    print("❌ Error processing response:", e)
