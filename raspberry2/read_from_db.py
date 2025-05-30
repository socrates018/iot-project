import requests
from requests.auth import HTTPBasicAuth
import getpass

# Define the InfluxDB IP and URL here

# InfluxDB IPs:
# Public: 194.177.207.38
# Local: 10.64.44.156
INFLUXDB_IP = "194.177.207.38"
INFLUXDB_URL = f"http://{INFLUXDB_IP}:8086"
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
    if response.status_code == 401:
        return None
    print("Insert data:", response.ok)
    return response

def query_data(db_name, user, password, measurement):
    query = f"SELECT * FROM {measurement}"
    response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
    if response.status_code == 401:
        return None
    print("Query result:", response.text)
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

def delete_data(db_name, user, password, measurement, condition="time < now()"):
    query = f"DELETE FROM {measurement} WHERE {condition}"
    response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
    if response.status_code == 401:
        return None
    print("Delete data:", response.text)

def main():
    student_user = "team19"
    student_pass = getpass.getpass("Enter InfluxDB password for team19: ")
    db_name = "team19_db"

    # Show topics and check password once
    auth_check = show_topics(db_name, student_user, student_pass)
    if auth_check is None:
        print("Authentication failed: Wrong username or password for InfluxDB. Exiting.")
        return

    action = input("Choose action: [1] Export data [2] Delete data (enter 1 or 2): ").strip()

    if action == "2":
        measurement = input("Enter measurement to delete (default: all): ").strip() or "all"
        condition = input("Enter delete condition (default: time < now()): ").strip() or "time < now()"
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
