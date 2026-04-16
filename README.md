# GL.inet Router Skill for OpenClaw

A Python-based skill for controlling and managing GL.inet routers (firmware 4.0+) via OpenClaw AI agent framework.

## Features

- 📱 **Client Management**: List all connected devices with bandwidth usage
- 🔒 **Block/Unblock**: Control internet access per device
- 🔄 **Reboot**: Immediate or scheduled router restart
- 📊 **Status Monitoring**: System health, memory, CPU temperature, modem signal strength
- 🌐 **Network Control**: Full router management via JSON-RPC API

## Project Structure

```
glinet-skill/
├── skills/
│   └── glinet_router/
│       ├── SKILL.md                 # OpenClaw skill documentation
│       ├── _meta.json               # Skill metadata
│       └── scripts/
│           └── glinet-router.py     # Main CLI script
├── requirements.txt                 # Python dependencies
├── .venv/                           # Virtual environment
└── README.md                        # This file
```

## Prerequisites

- Python 3.x
- GL.inet router running firmware **4.0 or newer**
- `python-glinet` library (handles JSON-RPC communication)
- Network access to router at `https://192.168.8.1/rpc` (default)

## Installation

### 1. Clone and Setup

```bash
cd glinet-skill
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Router Connection

```bash
python3 skills/glinet_router/scripts/glinet-router.py config
```

You'll be prompted for:
- **Router URL** (default: `https://192.168.8.1/rpc`)
- **Username** (default: `root`)
- **Password** (required - stored securely in `~/.glinet-skill/config.json`)

The script will test the connection before saving.

## Usage

All commands follow the same pattern:

```bash
python3 skills/glinet_router/scripts/glinet-router.py <command> [options]
```

### Commands

#### 📱 List Connected Clients
```bash
python3 skills/glinet_router/scripts/glinet-router.py clients
```

Output shows: MAC address, IP, upload/download speed, and any device comments.

#### 🔒 Block a Client
```bash
python3 skills/glinet_router/scripts/glinet-router.py block AA:BB:CC:DD:EE:FF
```

The blocked client cannot access the internet.

#### 🔓 Unblock a Client
```bash
python3 skills/glinet_router/scripts/glinet-router.py unblock AA:BB:CC:DD:EE:FF
```

Re-enables internet access for the device.

#### 🔄 Reboot Router

**Immediately:**
```bash
python3 skills/glinet_router/scripts/glinet-router.py reboot
```

**Schedule at specific time (24-hour format):**
```bash
python3 skills/glinet_router/scripts/glinet-router.py reboot --schedule 02:00
```

Scheduled reboot occurs daily at the specified time.

#### 📊 Check Status

**Full status (system + modem):**
```bash
python3 skills/glinet_router/scripts/glinet-router.py status
```

**System only** (uptime, memory, CPU temp, load, network mode):
```bash
python3 skills/glinet_router/scripts/glinet-router.py status system
```

**Modem only** (SIM status, carrier, signal strength):
```bash
python3 skills/glinet_router/scripts/glinet-router.py status modem
```

## Configuration

The configuration is stored at:
```
~/.glinet-skill/config.json
```

**Security Note**: The config file has restricted permissions (0600). Never share or commit this to version control.

### Example config.json:
```json
{
    "url": "https://192.168.8.1/rpc",
    "username": "root",
    "password": "your_secure_password"
}
```

## Integration with OpenClaw

This skill is designed as an OpenClaw skill module. The `SKILL.md` file contains:

- Natural language descriptions of all actions
- Input/output specifications
- Behavior rules for the AI agent
- Error handling guidelines
- Multi-language support (Polish examples included)

### How OpenClaw Uses It

1. AI agent reads `SKILL.md` to understand capabilities
2. User asks something like: "Pokaż mi urządzenia podłączone do routera"
3. AI parses request and calls: `python3 {baseDir}/scripts/glinet-router.py clients`
4. Script returns formatted data
5. AI presents results to user in natural language

## API Information

The skill uses the `python-glinet` library which communicates with 43+ API modules:

**Key modules used:**
- `clients` - Device management, bandwidth monitoring
- `system` - Router health, uptime, resources
- `modem` - 4G/LTE status, signal strength
- `reboot` - Scheduled and immediate restarts
- `network` - DHCP leases, ARP table

Full API documentation available in `~/.glinet-skill/venv/lib/python3.x/site-packages/pyglinet/api/api_description.json`

## Status Information Explained

### System Status Fields
- **Uptime**: How long the router has been running without restart
- **Memory**: RAM usage (used/total in MB and percentage)
- **CPU Temp**: Temperature of CPU cores in Celsius (overheating if > 85°C)
- **Load Average**: System load (3 values: 1min, 5min, 15min average)
- **Mode**: Operating mode (Router, WDS Bridge, Relay, Mesh, AP)
- **Server Time**: Current date and time on router

### Modem Status Fields
- **SIM Status**: 
  - Registered = SIM card ready and connected to network
  - Not registered = SIM detected but not connected
  - Locked = SIM requires PIN code
- **Carrier**: Mobile network operator name
- **Signal RSSI**: Power level in dBm (closer to 0 = stronger, e.g., -90 dBm is good)
- **Signal RSRP**: Reference signal power in dBm (modern metric, -100 dBm is good)
- **IMEI/IMSI**: Device and SIM identifiers (partially masked for privacy)

## Error Handling

### "No configuration found"
```
❌ Error: No configuration found.
👉 Please run setup first: python3 glinet-router.py config
```
→ Run the config command with router credentials

### "Connection failed"
```
❌ Connection failed: [error details]
```
→ Verify:
- Router is powered on
- URL is correct (check network settings)
- Username/password are accurate
- Firewall isn't blocking access

### "No clients connected"
```
✅ No clients connected
```
→ Normal - no devices currently using the router

## Development

### Running Tests

```bash
# Test client listing
python3 skills/glinet_router/scripts/glinet-router.py clients

# Test system status
python3 skills/glinet_router/scripts/glinet-router.py status system

# Test modem status
python3 skills/glinet_router/scripts/glinet-router.py status modem
```

### Adding New Features

1. Identify the GL.inet API endpoint in `api_description.json`
2. Add new command function in `glinet-router.py`
3. Update `SKILL.md` with new action description
4. Test with actual router

Example adding WiFi control:
```python
def cmd_wifi(router, args):
    """Toggle WiFi on/off"""
    result = router.request('call', ['', 'wifi', 'set_config', {
        'wifi': args.enabled
    }])
    print(f"✅ WiFi {'enabled' if args.enabled else 'disabled'}")
```

Then add to argparse and SKILL.md.

## Troubleshooting

### SSL Certificate Warnings
The skill disables SSL verification by default (`verify_ssl_certificate=False`) because GL.inet uses self-signed certificates. This is safe for local network access.

### Connection Timeouts
- Check router IP: `ping 192.168.8.1`
- Check firewall: Ensure port 443 (HTTPS) is accessible
- Increase timeout in script: `GlInet(..., timeout=30)`

### Rate Limiting
Multiple rapid requests may be throttled. Add delays:
```python
import time
time.sleep(2)  # Between operations
```

## License

GNU General Public License v3 (matching python-glinet)

## References

- [GL.inet Official](https://www.gl-inet.com/)
- [python-glinet GitHub](https://github.com/gl-inet/py-glinet)
- [OpenClaw Framework](https://openclaw.dev/)
