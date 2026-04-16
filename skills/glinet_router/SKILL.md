```skill
---
name: glinet_router
description: Control GL.inet router - manage clients, monitor status, reboot, and block/unblock devices.
metadata: {"openclaw":{"requires":{"bins":["python3"]}}}
---

# GL.inet Router Management

Use this skill to control and manage your GL.inet router (firmware 4.0+).

## Command path

- Script: `{baseDir}/scripts/glinet-router.py`

## Supported actions

### Setup & Configuration
- Configure connection: `python3 {baseDir}/scripts/glinet-router.py config`

### Client Management
- List all clients: `python3 {baseDir}/scripts/glinet-router.py clients`
- Block client: `python3 {baseDir}/scripts/glinet-router.py block <MAC or IP>`
- Unblock client: `python3 {baseDir}/scripts/glinet-router.py unblock <MAC or IP>`
  - Note: Blocking supports either a MAC address or an IP address. The skill uses the router API `black_white_list.set_single_mac` to update the router blacklist and also keeps a local cache (`~/.glinet-skill/blocked.json`) so the CLI shows blocked status immediately.

### Router Control
- Reboot immediately: `python3 {baseDir}/scripts/glinet-router.py reboot`
- Schedule reboot: `python3 {baseDir}/scripts/glinet-router.py reboot --schedule HH:MM`

### Status & Monitoring
- Full status: `python3 {baseDir}/scripts/glinet-router.py status`
- System status only: `python3 {baseDir}/scripts/glinet-router.py status system`
- Modem status only: `python3 {baseDir}/scripts/glinet-router.py status modem`

## Client list output description

Listed in columns:
- **Device Name**: Device name (alias), hostname, or MAC address if no name is set
- **IP**: Current DHCP-assigned IP address
- **Total ↓**: Total download traffic since device connected (in MB/GB)
- **Total ↑**: Total upload traffic since device connected (in MB/GB)
- **Speed ↓**: Current download speed (real-time, in KB/s or MB/s)
- **Speed ↑**: Current upload speed (real-time, in KB/s or MB/s)
- **Status**: Device status
  - 🟢 Online = Device currently connected and using internet
  - ⚪ Offline = Device previously connected but now offline
  - 🔴 Blocked = Device is blocked and cannot access internet. NOTE: the router's API may not always reflect the blocked flag in its client list, so this skill maintains a local blacklist cache to display blocked status reliably in the CLI.

## Behavior rules

### Initial Setup
- If `~/.glinet-skill/config.json` is missing, tell user to run: `python3 {baseDir}/scripts/glinet-router.py config`
- User must provide router password during config (stored securely)
- Default router URL is `https://192.168.8.1/rpc`

### Client Management
- MAC addresses are case-insensitive but always convert to UPPERCASE
- Blocked clients cannot access the internet
- When user asks to block/unblock, always confirm the device by showing its IP
- If multiple similar device names exist, ask for clarification by MAC or IP address

### Reboot Operations
- Always warn before immediate reboot: "This will restart the router immediately. Continue? (yes/no)"
- For scheduled reboots, explain the schedule clearly: "Reboot will occur daily at HH:MM"
- When scheduling, provide HH:MM in 24-hour format
- After reboot command, confirm: "Router will restart in a few seconds. You may lose connection."

### Status Information
- System status includes: uptime, memory usage, CPU temperature, load average, network mode, current time
- Modem status includes: SIM card status, carrier name, signal strength (RSSI/RSRP), IMEI
- If no modem is detected, clearly state "No LTE/4G modem found"
- Temperature is in Celsius
- Signal RSSI/RSRP values: stronger (less negative) = better signal

### Error Handling
- If connection fails during config, show error and ask user to verify:
  - Router is powered on and accessible at the URL
  - Username/password are correct
  - SSL certificate verification (disabled by default for self-signed certs)
- Invalid MAC format should be caught with: "Invalid MAC address format"
- Rate limiting: wait 2-3 seconds between multiple client operations

## Language support

- Polish instructions should be provided to Polish-speaking users
- Output field names (MAC, IP, Upload, Download) are in English
- Status table is always in English for consistency

## Examples

### Example 1: List clients and block suspicious one
```
User: "Pokaż mi jakie urządzenia są podłączone"
AI: "Pokazuję listę urządzeń podłączonych do routera"
[runs: python3 {baseDir}/scripts/glinet-router.py clients]
[displays table with 3 devices]
User: "Zablokuj to drugie"
AI: "Biorę MAC adres drugiego urządzenia i blokuję je"
[runs: python3 {baseDir}/scripts/glinet-router.py block AA:BB:CC:DD:EE:FF]
AI: "Urządzenie AA:BB:CC:DD:EE:FF zostało zablokowane"
```

### Example 2: Monitor router status
```
User: "Jak się ma mój router?"
AI: "Sprawdzam status routera"
[runs: python3 {baseDir}/scripts/glinet-router.py status]
[shows system status with uptime, memory, CPU temp]
[shows modem status with signal strength]
AI: "Twój router pracuje już 5 dni. Pamięć: 45%, Temperatur CPU: 62°C. Sygnał LTE: -95 dBm"
```

### Example 3: Schedule reboot
```
User: "Zaplanuj restart routera na 2 w nocy"
AI: "Planuję restart na 02:00"
[runs: python3 {baseDir}/scripts/glinet-router.py reboot --schedule 02:00]
AI: "Router będzie restartowany codziennie o 02:00"
```

## Configuration file

Location: `~/.glinet-skill/config.json`

Contents:
```json
{
    "url": "https://192.168.8.1/rpc",
    "username": "root",
    "password": "your_password_here"
}
```

**Important**: Config file is encrypted with restrictive file permissions (0600). Never share or commit to version control.
```
