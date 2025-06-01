import requests
from requests.auth import HTTPBasicAuth
import getpass
import os

# Define the InfluxDB IP and URL here

# InfluxDB IPs:
# Public: 194.177.207.38
# Local: 10.64.44.156
INFLUXDB_IP = "194.177.207.38"
INFLUXDB_URL = f"http://{INFLUXDB_IP}:8086"
ADMIN_USER = "username"
ADMIN_PASS = "password"  # No longer hardcoded

# ---------- Load or prompt for password ----------
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
INFLUX_PASSWORD = None
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('MQTT_PASSWORD='):
                INFLUX_PASSWORD = line.strip().split('=', 1)[1]
                break
if not INFLUX_PASSWORD:
    INFLUX_PASSWORD = getpass.getpass("Enter InfluxDB password for team19: ")
    with open(ENV_PATH, 'a') as f:
        f.write(f"MQTT_PASSWORD={INFLUX_PASSWORD}\n")

def insert_data(db_name, user, password, measurement, value, timestamp=None):
    line = f"{measurement} value={value}"
    if timestamp:
        line += f" {timestamp}"
    response = requests.post(f"{INFLUXDB_URL}/write", 
                            params={"db": db_name},
                            data=line,
                            auth=HTTPBasicAuth(user, password))
    if response.status_code == 401:
        return None
    print("Insert data:", response.ok)
    return response

def query_data(db_name, user, password, measurement):
    # Add quotes for measurement names that are not purely alphabetic (e.g., contain numbers)
    if not measurement.isalpha():
        measurement_quoted = f'"{measurement}"'
    else:
        measurement_quoted = measurement
    query = f"SELECT * FROM {measurement_quoted}"
    response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
    if response.status_code == 401:
        return None
    return response

def show_topics(db_name, user, password):
    query = "SHOW MEASUREMENTS"
    response = requests.get(
        f"{INFLUXDB_URL}/query",
        params={"db": db_name, "q": query},
        auth=HTTPBasicAuth(user, password)
    )
    if response.status_code == 401:
        return None
    print("Topics:")
    try:
        data = response.json()
        results = data.get("results", [])
        if results and "series" in results[0]:
            for entry in results[0]["series"][0]["values"]:
                if entry and len(entry) > 0:
                    print("-", entry[0])
        else:
            print("No measurements found in the database.")
    except Exception as e:
        print("Error processing topics response:", e)
    return response

def parse_time_to_ns(timestr):
    """
    Convert a string in the format YYYY/M/D:H:M (accepts single or double digits) to nanoseconds since epoch (int).
    Example: '2025/6/1:0:0' or '2025/06/01:00:00' -> 1746038400000000000
    """
    import datetime
    parts = timestr.replace('/', ' ').replace(':', ' ').split()
    year, month, day, hour, minute = [int(p) for p in parts]
    dt = datetime.datetime(year, month, day, hour, minute)
    return int(dt.timestamp() * 1_000_000_000)

def delete_data(db_name, user, password, measurement, condition="time < now()"):
    # If the condition contains a time in YYYY/M/D:H:M, convert it to ns
    import re
    match = re.search(r"(\d{4}/\d{1,2}/\d{1,2}:\d{1,2}:\d{1,2})", condition)
    if match:
        ns = parse_time_to_ns(match.group(1))
        condition = re.sub(r"\d{4}/\d{1,2}/\d{1,2}:\d{1,2}:\d{1,2}", str(ns), condition)
    query = f"DELETE FROM {measurement} WHERE {condition}"
    response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
    if response.status_code == 401:
        return None
    print("Delete data:", response.text)

def main():
    student_user = "team19"
    student_pass = INFLUX_PASSWORD
    db_name = "team19_db"

    # Show topics and check password once
    auth_check = show_topics(db_name, student_user, student_pass)
    if auth_check is None:
        print("Authentication failed: Wrong username or password for InfluxDB. Exiting.")
        return

    action = input("Choose action: [1] Export data [2] Delete data (enter 1 or 2): ").strip()

    if action == "2":
        measurement = input("Enter measurement to delete (default: all): ").strip() or "all"
        raw_condition = input("Enter delete time (YYYY/M/D:H:M) or custom condition (default: before now): ").strip()
        # Determine the condition
        if not raw_condition:
            condition = "time < now()"
        elif raw_condition.count(":") == 2 and raw_condition.count("/") == 2:
            # Looks like a date/time string
            condition = f"time < {raw_condition}"
        else:
            # Assume user entered a custom condition
            condition = raw_condition
        if measurement == "all":
            all_measurements_json = auth_check.json()
            measurement_names = [entry[0] for entry in all_measurements_json.get("results", [])[0]["series"][0]["values"]]
        else:
            measurement_names = [measurement]
        if not measurement_names:
            print("No measurements found to delete.")
            return
        for m in measurement_names:
            delete_data(db_name, student_user, student_pass, m, condition)
            print(f"Delete command sent for measurement '{m}' with condition '{condition}'.")
        return

    # Export data
    measurement = input("Enter measurement to export (default: all): ").strip() or "all"
    if measurement == "all":
        all_measurements_json = auth_check.json()
        measurement_names = [entry[0] for entry in all_measurements_json.get("results", [])[0]["series"][0]["values"]]
        for m in measurement_names:
            try:
                response = query_data(db_name, student_user, student_pass, m)
                data = response.json()
                results = data.get("results", [])
                if results and "series" in results[0]:
                    with open(f"{m}.txt", "w", encoding="utf-8") as f:
                        import json
                        json.dump(results[0]["series"], f, indent=2)
                    print(f"{m} exported to '{m}.txt'.")
                else:
                    print(f"No data found for {m}.")
            except Exception as e:
                print(f"Error processing {m}: {e}")
    else:
        response = query_data(db_name, student_user, student_pass, measurement)
        if response:
            try:
                data = response.json()
                results = data.get("results", [])
                if results and "series" in results[0]:
                    with open(f"{measurement}.txt", "w", encoding="utf-8") as f:
                        import json
                        json.dump(results[0]["series"], f, indent=2)
                    print(f"{measurement} exported to '{measurement}.txt'.")
                else:
                    print(f"No {measurement} found in the database.")
            except Exception as e:
                print("Error processing response:", e)

if __name__ == "__main__":
    main()
