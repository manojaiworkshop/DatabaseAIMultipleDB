# DatabaseAI Test Queries Reference

This document contains complex NLP queries to test your DatabaseAI system with the Network Management Database.

## Database Schema Overview

### 5 Interconnected Tables:

1. **hardware_info** - Hardware specifications
   - Columns: hardware_id, manufacturer, model, type, cpu_cores, ram_gb, storage_gb, warranty_end, purchase_date, cost

2. **device_status** - Status codes and descriptions
   - Columns: status_id, status_name, description, color_code

3. **network_devices** - Network equipment inventory
   - Columns: device_id, device_name, device_type, ip_address, mac_address, location, building, hardware_id (FK), status_id (FK)

4. **maintenance_logs** - Maintenance history
   - Columns: log_id, device_id (FK), maintenance_type, performed_by, maintenance_date, duration_hours, cost, next_maintenance_date

5. **network_alerts** - Alert and incident tracking
   - Columns: alert_id, device_id (FK), alert_type, severity, alert_time, resolved, resolved_by, resolution_time

## Test Queries (Copy & Paste into DatabaseAI)

### 1. Basic Multi-Table JOIN
```
Show me all network devices with their hardware information
```

### 2. Aggregation with Filtering
```
Which devices have had more than 2 critical alerts?
```

### 3. Status-Based Query
```
List all Cisco devices that are currently offline
```

### 4. Cost Analysis
```
Show total maintenance cost per building
```

### 5. Date-Based Filtering
```
Which devices need maintenance in the next 30 days?
```

### 6. Complex JOIN with Multiple Tables
```
Show me devices with critical alerts that have Cisco hardware and are in Building A
```

### 7. Technician Performance
```
Which technician performed the most maintenance tasks?
```

### 8. High CPU Usage Analysis
```
Show me all routers with CPU usage above 70%
```

### 9. Alert Resolution Time
```
What's the average time to resolve critical alerts per device type?
```

### 10. VIEW Creation (Most Complex)
```
Create a view showing device health status including hardware info, current alerts, and last maintenance date
```

### 11. Uptime Analysis
```
Which devices have uptime less than 500 hours and have had recent maintenance?
```

### 12. Manufacturer Comparison
```
Compare maintenance costs between Dell and Cisco hardware
```

### 13. Unresolved Issues
```
Show all unresolved critical alerts with device location and hardware type
```

### 14. Bandwidth Analysis
```
Which building has the highest total bandwidth usage?
```

### 15. Complex Filtering
```
Find all firewalls and switches in Building B with more than 16GB RAM that had maintenance in the last 90 days
```

### 16. Cost Per Device Type
```
What's the average maintenance cost per device type?
```

### 17. Alert Frequency
```
Which device has the most alerts in the last month?
```

### 18. Hardware Under Warranty
```
Show me all hardware that's still under warranty with their device locations
```

### 19. Memory Usage Correlation
```
Find devices with high memory usage that also have critical alerts
```

### 20. Type Mismatch Challenge (Tests Error Recovery)
```
Create a view joining network devices and maintenance logs showing device name and technician
```
*This should trigger the type mismatch error your agent should intelligently resolve*

## Expected Agent Behaviors to Test

### ✅ Should Successfully Handle:
1. Multi-table JOINs (2-4 tables)
2. Aggregation functions (COUNT, SUM, AVG)
3. Date arithmetic and filtering
4. GROUP BY with multiple columns
5. Subqueries
6. VIEW creation
7. Complex WHERE clauses

### 🔧 Should Intelligently Recover From:
1. Type mismatches in JOIN conditions (INTEGER vs VARCHAR)
2. Non-existent table names (should suggest similar names)
3. Non-existent column names (should show available columns)
4. Syntax errors (should fix on retry)
5. Token limit exceeded (should use compact schema)

## Testing Checklist

- [ ] Test basic SELECT with single table
- [ ] Test 2-table JOIN
- [ ] Test 3-table JOIN
- [ ] Test 4-table JOIN (all tables)
- [ ] Test COUNT/SUM/AVG aggregations
- [ ] Test GROUP BY queries
- [ ] Test date filtering (BETWEEN, >, <)
- [ ] Test VIEW creation
- [ ] Test queries that should trigger type cast errors
- [ ] Test queries with non-existent columns (error recovery)
- [ ] Test queries with non-existent tables (error recovery)
- [ ] Test queries that exceed token limits (compact mode)
- [ ] Test multiple retries with progressive error fixing

## Success Metrics

Your agent is working well if:
- ✅ Basic queries succeed on first attempt
- ✅ Complex JOINs succeed within 1-2 retries
- ✅ Type mismatch errors are auto-fixed with proper casting
- ✅ Error messages provide clear hints
- ✅ Retry count is displayed to user
- ✅ Results are displayed in a clean table format

## Data Statistics
- Hardware records: 10
- Device status codes: 5
- Network devices: 10
- Maintenance logs: 15
- Network alerts: 20

## Foreign Key Relationships
```
network_devices.hardware_id → hardware_info.hardware_id
network_devices.status_id → device_status.status_id
maintenance_logs.device_id → network_devices.device_id
network_alerts.device_id → network_devices.device_id
```

---

**Tip:** Start with simple queries and gradually increase complexity to test the agent's capabilities!
