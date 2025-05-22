## Bash-based introduction to Influx DB (using curl command)

### Create User

```bash
curl -G -u username:'password' http://localhost:8086/query --data-urlencode "q=CREATE USER <user> WITH PASSWORD 'password'"
```

### Create Database

```bash
curl -G -u username:'password' http://localhost:8086/query --data-urlencode "q=CREATE DATABASE <db_name>"
```

### Give Privileges to the User (GRANT)

```bash
curl -G -u username:'password' http://localhost:8086/query --data-urlencode "q=GRANT ALL ON <db_name> TO <user>"
```

### Insert New Data Point

```bash
curl -i -u username:'password' -XPOST "http://localhost:8086/write?db=test" --data-binary "air_temperature value=22.5"
```

### Query Data from DB

```bash
curl -G -u username:'password' "http://localhost:8086/query" --data-urlencode "db=test" --data-urlencode "q=SELECT * FROM air_temperature"
```

### Update Value

```bash
curl -i -u username:'password' -XPOST "http://localhost:8086/write?db=test" --data-binary "air_temperature value=23.0 <same timestamp>"
```

### Delete Data

```bash
curl -G -u username:'password' "http://localhost:8086/query" --data-urlencode "db=test" --data-urlencode "q=DELETE FROM temperature WHERE time < now()"
```
