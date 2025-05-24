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

def show_measurements(db_name, user, password):
    query = "SHOW MEASUREMENTS"
    response = requests.get(
        f"{INFLUXDB_URL}/query",
        params={"db": db_name, "q": query},
        auth=HTTPBasicAuth(user, password)
    )
    print("Measurements:", response.text)
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

# Query all data from measurement (specific category e.g. air_temperature)
response = query_data(db_name, student_user, student_pass, measurement)
# Query all data 
all_data = show_measurements(db_name, student_user, student_pass)

# Check if data exists and print confirmation
try:
    data = response.json()
    results = data.get("results", [])
    if results and "series" in results[0]:
        print("✅ Data found in the database.")
        # Save all data to a local file
        with open(f"{measurement}.txt", "w", encoding="utf-8") as f:
            import json
            json.dump(results[0]["series"], f, indent=2)
        print(f"{measurement} exported to 'exported_data.txt'.")
    else:
        print(f"No {measurement} found in the database.")
except Exception as e:
    print("❌ Error processing response:", e)

# Export measurements to a second file
try:
    all_measurements = all_data.json()
    measurements_results = all_measurements.get("results", [])
    if measurements_results and "series" in measurements_results[0]:
        with open("all_data.txt", "w", encoding="utf-8") as f:
            import json
            json.dump(measurements_results[0]["series"], f, indent=2)
        print("📁 All measurements exported to 'all_data.txt'.")
    else:
        print("⚠️ No measurements found in the database.")
except Exception as e:
    print("❌ Error processing measurements response:", e)
