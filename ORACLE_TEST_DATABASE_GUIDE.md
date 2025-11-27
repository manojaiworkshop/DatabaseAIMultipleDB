# Oracle Network Management Test Database

## 📋 Overview

This script creates a complete **Network Management Database** in Oracle with 5 interconnected tables and sample data for testing DatabaseAI's natural language query capabilities.

## 🗄️ Database Schema

### Tables Created

1. **hardware_info** (10 records)
   - Hardware specifications and purchase information
   - Fields: hardware_id, hardware_type, manufacturer, model_number, purchase_date, warranty_years, unit_price, supplier

2. **device_status** (5 records)
   - Device operational states
   - Fields: status_id, status_name, status_description, severity_level

3. **network_devices** (10 records)
   - Main devices table with performance metrics
   - Fields: device_id, device_name, hardware_id (FK), status_id (FK), ip_address, location, floor_number, building, installation_date, last_maintenance_date, uptime_hours, cpu_usage_percent, memory_usage_percent, bandwidth_usage_mbps

4. **maintenance_logs** (15 records)
   - Historical maintenance records
   - Fields: log_id, device_id (FK), maintenance_type, performed_by, maintenance_date, duration_hours, cost, description, issues_found, actions_taken, next_maintenance_date

5. **network_alerts** (20 records)
   - Alert tracking and resolution
   - Fields: alert_id, device_id (FK), alert_type, severity, alert_message, alert_timestamp, acknowledged, acknowledged_by, acknowledged_at, resolved, resolved_at, resolution_notes

## 🚀 Quick Start

### Method 1: Run Shell Script (Recommended)
```bash
./setup_oracle_test_db.sh
```

### Method 2: Run Python Script Directly
```bash
python3 test_network_management_oracle.py
```

### Method 3: Custom Configuration
```bash
export ORACLE_USER="myuser"
export ORACLE_PASSWORD="mypassword"
export ORACLE_DSN="localhost:1521/XE"
./setup_oracle_test_db.sh
```

## 📦 Prerequisites

1. **Oracle Database Running**
   ```bash
   docker compose -f docker-compose.oracle.yml up
   ```

2. **Oracle User Created**
   ```bash
   ./create_oracle_user.sh
   ```
   Default user: `pgaiview/pgaiview123`

3. **Python Dependencies**
   ```bash
   pip install oracledb
   ```

## 🎯 Sample Test Queries

Once the database is set up, try these natural language queries in DatabaseAI:

### Basic Queries

1. "Show me all network devices"
2. "List all routers and their IP addresses"
3. "What's the status of all devices?"
4. "Show me devices in Building A"

### Join Queries

5. "Show me all network devices with their hardware information"
6. "List all Cisco devices with their current status"
7. "What devices are made by HP or Dell?"

### Aggregation Queries

8. "Show total maintenance cost per building"
9. "Which technician has performed the most maintenance?"
10. "What's the average CPU usage by device type?"

### Complex Queries

11. "Show me all routers and firewalls in Building A with CPU usage above 70% that have unresolved critical alerts"
12. "Which devices have had more than 2 critical alerts in the last month?"
13. "What's the total cost of ownership for each device including purchase price and maintenance?"
14. "Rank devices by CPU usage and show the top 5 with their hardware type"
15. "Which devices need maintenance in the next 30 days based on their last maintenance date?"

### Advanced Analytics

16. "Find devices where high CPU usage correlates with multiple maintenance events"
17. "Show me the distribution of device types across all buildings with their average bandwidth usage"
18. "Which devices have both high memory usage and low uptime hours indicating potential problems?"
19. "What's the average cost of maintenance per hardware manufacturer?"
20. "Which technician resolved the most alerts in the last 6 months?"

## 🔍 Verify Database

After setup, verify the data:

```bash
python3 -c "
import oracledb
conn = oracledb.connect(user='pgaiview', password='pgaiview123', dsn='localhost:1521/XE')
cursor = conn.cursor()

# List all tables
cursor.execute('SELECT table_name FROM user_tables ORDER BY table_name')
for row in cursor:
    print(f'Table: {row[0]}')
    
# Count records
tables = ['HARDWARE_INFO', 'DEVICE_STATUS', 'NETWORK_DEVICES', 'MAINTENANCE_LOGS', 'NETWORK_ALERTS']
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    print(f'{table}: {cursor.fetchone()[0]} records')
    
cursor.close()
conn.close()
"
```

## 🗑️ Clean Up / Reset Database

To drop all tables and start fresh:

```sql
DROP TABLE network_alerts CASCADE CONSTRAINTS;
DROP TABLE maintenance_logs CASCADE CONSTRAINTS;
DROP TABLE network_devices CASCADE CONSTRAINTS;
DROP TABLE device_status CASCADE CONSTRAINTS;
DROP TABLE hardware_info CASCADE CONSTRAINTS;

DROP SEQUENCE network_alerts_seq;
DROP SEQUENCE maintenance_logs_seq;
DROP SEQUENCE network_devices_seq;
DROP SEQUENCE device_status_seq;
DROP SEQUENCE hardware_info_seq;
```

Or simply run the script again - it will drop and recreate everything.

## 📊 Data Statistics

- **10 Hardware Items**: Routers, Switches, Firewalls, Access Points, Servers
- **5 Device Statuses**: Online, Offline, Maintenance, Warning, Critical
- **10 Network Devices**: Across 2 buildings and data center
- **15 Maintenance Records**: Various types (Routine, Upgrade, Update, Repair, Tuning)
- **20 Network Alerts**: Different severities with acknowledgment and resolution tracking

## 🔗 Integration with DatabaseAI

### Update config.yml

```yaml
database:
  type: oracle
  host: localhost
  port: 1521
  service_name: XE
  user: pgaiview
  password: pgaiview123
```

### Or use connection string:
```
oracle://pgaiview:pgaiview123@localhost:1521/XE
```

## 💡 Key Features

✅ **Foreign Key Relationships** - Tests JOIN operations  
✅ **Multiple Data Types** - VARCHAR2, NUMBER, DATE, TIMESTAMP  
✅ **Realistic Data** - Network management scenarios  
✅ **Complex Queries** - Multi-table joins, aggregations, window functions  
✅ **Performance Metrics** - CPU, memory, bandwidth usage  
✅ **Time-based Data** - Dates, timestamps for temporal queries  
✅ **Status Tracking** - Alerts, maintenance, device states

## 🐛 Troubleshooting

### Connection Error
```
ORA-12541: TNS:no listener
```
**Solution**: Start Oracle database
```bash
docker compose -f docker-compose.oracle.yml up
```

### User Not Found
```
ORA-01017: invalid username/password
```
**Solution**: Create the Oracle user first
```bash
./create_oracle_user.sh
```

### Module Not Found
```
ModuleNotFoundError: No module named 'oracledb'
```
**Solution**: Install oracledb
```bash
pip install oracledb
```

## 📝 Notes

- Oracle sequences are used for auto-increment IDs (instead of SERIAL in PostgreSQL)
- Boolean fields use NUMBER(1) with 0/1 values (Oracle doesn't have native BOOLEAN)
- VARCHAR2 is used instead of VARCHAR (Oracle best practice)
- CASCADE CONSTRAINTS is used when dropping tables with foreign keys
- All tables are created in the user's default schema (no schema prefix needed)

## 🔄 Comparison with PostgreSQL Version

This Oracle version mirrors the PostgreSQL `test_network_management_db.py` with Oracle-specific adaptations:

| Feature | PostgreSQL | Oracle |
|---------|-----------|--------|
| Auto-increment | SERIAL | SEQUENCE + NEXTVAL |
| Boolean | BOOLEAN | NUMBER(1) |
| String type | VARCHAR | VARCHAR2 |
| Text type | TEXT | VARCHAR2(500+) |
| Drop cascade | CASCADE | CASCADE CONSTRAINTS |

## 📞 Support

For issues with:
- **Oracle setup**: Check `ORACLE_USER_CREATION_GUIDE.md`
- **Database connection**: Verify docker-compose.oracle.yml settings
- **Sample data**: Review test_network_management_oracle.py script
