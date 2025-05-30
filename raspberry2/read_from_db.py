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

def show_topics(db_name, user, password):
    query = "SHOW MEASUREMENTS"
    response = requests.get(
        f"{INFLUXDB_URL}/query",
        params={"db": db_name, "q": query},
        auth=HTTPBasicAuth(user, password)
    )
    print("Topics:", response.text)
    return response

def delete_data(db_name, user, password, condition="time < now()"):
    query = f"DELETE FROM {measurement} WHERE {condition}"
    response = requests.get(f"{INFLUXDB_URL}/query",
                          params={"db": db_name, "q": query},
                          auth=HTTPBasicAuth(user, password))
    print("Delete data:", response.text)

def main():
    student_user = "team19"
    student_pass = getpass.getpass("Enter InfluxDB password for team19: ")
    db_name = "team19_db"
    measurement = input("Enter measurement to export (default: all): ").strip() or "all"

    if measurement == "all":
        # Get all measurement names
        all_measurements_resp = show_topics(db_name, student_user, student_pass)
        all_measurements_json = all_measurements_resp.json()
        measurement_names = []
        try:
            results = all_measurements_json.get("results", [])
            if results and "series" in results[0]:
                for entry in results[0]["series"][0]["values"]:
                    if entry and len(entry) > 0:
                        measurement_names.append(entry[0])
        except Exception as e:
            print("Error extracting measurement names:", e)
        # Query and collect all measurements
        all_data = {}
        for m in measurement_names:
            try:
                response = query_data(db_name, student_user, student_pass, m)
                data = response.json()
                results = data.get("results", [])
                if results and "series" in results[0]:
                    print(f"Data found for {m}.")
                    all_data[m] = results[0]["series"]
                else:
                    print(f"No data found for {m}.")
            except Exception as e:
                print(f"Error processing {m}: {e}")
        # Save all measurements to a single file
        if all_data:
            with open("all_measurements.txt", "w", encoding="utf-8") as f:
                import json
                json.dump(all_data, f, indent=2)
            print("All measurements exported to 'all_measurements.txt'.")
        else:
            print("No measurements found in the database.")
    else:
        response = query_data(db_name, student_user, student_pass, measurement)
        all_data = show_topics(db_name, student_user, student_pass)

        if response:
            try:
                data = response.json()
                results = data.get("results", [])
                if results and "series" in results[0]:
                    print("Data found in the database.")
                    with open(f"{measurement}.txt", "w", encoding="utf-8") as f:
                        import json
                        json.dump(results[0]["series"], f, indent=2)
                    print(f"{measurement} exported to '{measurement}.txt'.")
                else:
                    print(f"No {measurement} found in the database.")
            except Exception as e:
                print("Error processing response:", e)

        try:
            all_measurements = all_data.json()
            measurements_results = all_measurements.get("results", [])
            if measurements_results and "series" in measurements_results[0]:
                with open("show_topics.txt", "w", encoding="utf-8") as f:
                    import json
                    json.dump(measurements_results[0]["series"], f, indent=2)
                print("All measurements exported to 'show_topics.txt'.")
            else:
                print("No measurements found in the database.")
        except Exception as e:
            print("Error processing measurements response:", e)

if __name__ == "__main__":
    main()
