#!/usr/bin/env python3
"""
GL.inet Router Skill - Control your GL.inet router via CLI
Supports: client management, reboot, status checks
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from pyglinet import GlInet

# Configuration constants
CONFIG_DIR = Path.home() / '.glinet-skill'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Default router settings
DEFAULT_URL = 'https://192.168.8.1/rpc'
DEFAULT_USERNAME = 'root'

def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_config(config):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    os.chmod(CONFIG_FILE, 0o600)  # Restrict permissions

def load_config():
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        print("❌ Error: No configuration found.")
        print("👉 Please run setup first: python3 glinet-router.py config")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def do_config():
    """Interactive configuration setup."""
    print("=== GL.inet Router Setup ===\n")
    
    url = input(f"Router URL [{DEFAULT_URL}]: ").strip() or DEFAULT_URL
    username = input(f"Username [{DEFAULT_USERNAME}]: ").strip() or DEFAULT_USERNAME
    password = input("Password: ").strip()
    
    if not password:
        print("❌ Password is required!")
        sys.exit(1)
    
    # Test connection
    print("\n🔐 Testing connection...")
    try:
        router = GlInet(url=url, username=username, password=password, verify_ssl_certificate=False)
        router.login()
        print("✅ Connection successful!")
        router.logout()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    config = {
        'url': url,
        'username': username,
        'password': password
    }
    
    save_config(config)
    print(f"✅ Configuration saved to {CONFIG_FILE}\n")

def get_router():
    """Get authenticated router instance."""
    config = load_config()
    router = GlInet(
        url=config['url'],
        username=config['username'],
        password=config['password'],
        verify_ssl_certificate=False
    )
    router.login()
    return router

def cmd_clients(router, args):
    """List connected clients and their bandwidth usage."""
    print("📱 Getting client list...\n")
    
    result = router.request('call', ['', 'clients', 'get_list'])
    clients = result.data.get('clients', [])
    
    if not clients:
        print("✅ No clients connected")
        return
    
    print(f"{'MAC Address':<20} {'IP Address':<15} {'↑ Upload':<12} {'↓ Download':<12} {'Commented':<20}")
    print("-" * 90)
    
    for client in clients:
        mac = client.get('mac', 'N/A')
        ip = client.get('ip', 'N/A')
        tx = client.get('tx', 0)
        rx = client.get('rx', 0)
        comment = client.get('comment', '')
        
        # Convert bytes/sec to more readable format
        tx_str = format_bandwidth(tx)
        rx_str = format_bandwidth(rx)
        comment_str = comment[:18] if comment else ''
        
        print(f"{mac:<20} {ip:<15} {tx_str:<12} {rx_str:<12} {comment_str:<20}")

def cmd_block(router, args):
    """Block or unblock a client by MAC address."""
    if not args.mac:
        print("❌ MAC address required for block/unblock")
        sys.exit(1)
    
    mac = args.mac.upper()
    block = args.command == 'block'
    action = "Blocking" if block else "Unblocking"
    
    print(f"{action} client {mac}...\n")
    
    result = router.request('call', ['', 'clients', 'block_client', {
        'mac': mac,
        'block': block
    }])
    
    if result.data:
        err_code = result.data.get('err_code', 0)
        err_msg = result.data.get('err_msg', '')
        if err_code != 0:
            print(f"❌ Error {err_code}: {err_msg}")
            sys.exit(1)
    
    action_past = "blocked" if block else "unblocked"
    print(f"✅ Client {mac} {action_past} successfully!\n")

def cmd_reboot(router, args):
    """Reboot the router immediately or schedule it."""
    if args.schedule:
        # Parse scheduled reboot time
        try:
            hour, minute = args.schedule.split(':')
            hour, minute = int(hour), int(minute)
            
            if not (0 <= hour < 24 and 0 <= minute < 60):
                print("❌ Invalid time format. Use HH:MM (24-hour format)")
                sys.exit(1)
            
            print(f"📅 Scheduling reboot at {hour:02d}:{minute:02d}...\n")
            
            # Get current config and update it
            router.request('call', ['', 'reboot', 'set_config', {
                'hour': str(hour),
                'min': str(minute),
                'enable': True,
                'week': [0, 1, 2, 3, 4, 5, 6]  # Every day
            }])
            
            print(f"✅ Reboot scheduled for {hour:02d}:{minute:02d} daily!\n")
        except ValueError:
            print("❌ Invalid time format. Use HH:MM")
            sys.exit(1)
    else:
        # Immediate reboot
        print("🔄 Rebooting router immediately...\n")
        try:
            router.request('call', ['', 'system', 'reboot'])
            print("✅ Reboot command sent!\n")
        except Exception as e:
            print(f"❌ Reboot failed: {e}\n")
            sys.exit(1)

def cmd_status(router, args):
    """Show router status (system, modem, or all)."""
    what = args.what or 'all'
    
    if what in ['system', 'all']:
        print_system_status(router)
        print()
    
    if what in ['modem', 'all']:
        print_modem_status(router)

def print_system_status(router):
    """Print system status."""
    print("🖥️  SYSTEM STATUS\n")
    
    result = router.request('call', ['', 'system', 'get_status'])
    system_info = result.data.get('system', {})
    
    # Uptime
    uptime = system_info.get('uptime', 0)
    uptime_str = format_uptime(uptime)
    print(f"  ⏱️  Uptime:         {uptime_str}")
    
    # Memory
    memory = system_info.get('memory', {})
    mem_used = memory.get('used', 0)
    mem_total = memory.get('total', 0)
    if mem_total > 0:
        mem_percent = (mem_used / mem_total) * 100
        print(f"  💾 Memory:        {mem_used}/{mem_total} MB ({mem_percent:.1f}%)")
    
    # CPU
    cpu_temps = system_info.get('cpu_temps', {})
    if cpu_temps:
        for core, temp in cpu_temps.items():
            print(f"  🌡️  {core}:          {temp}°C")
    
    # Load average
    load_average = system_info.get('load_average', [])
    if load_average:
        print(f"  📊 Load avg:      {load_average[0]:.2f} {load_average[1]:.2f} {load_average[2]:.2f}")
    
    # Network mode
    modes = {0: 'Router', 1: 'WDS Bridge', 2: 'Relay Bridge', 3: 'Mesh', 4: 'AP'}
    mode = system_info.get('mode', 0)
    print(f"  📡 Mode:          {modes.get(mode, 'Unknown')}")
    
    # Timestamp
    timestamp = system_info.get('timestamp', 0)
    if timestamp > 0:
        dt = datetime.fromtimestamp(timestamp)
        print(f"  🕐 Server time:   {dt.strftime('%Y-%m-%d %H:%M:%S')}")

def print_modem_status(router):
    """Print modem status."""
    print("📱 MODEM STATUS\n")
    
    result = router.request('call', ['', 'modem', 'get_status'])
    modems = result.data.get('modems', [])
    
    if not modems:
        print("  ❌ No modem detected\n")
        return
    
    for i, modem in enumerate(modems):
        print(f"  Modem {i+1}:")
        
        # SIM card info
        simcard = modem.get('simcard', {})
        if simcard:
            sim_status = simcard.get('status', -1)
            status_map = {0: 'Registered', 1: 'Not registered', 2: 'Locked'}
            print(f"    🃏 SIM:          {status_map.get(sim_status, 'Unknown')}")
            
            carrier = simcard.get('carrier', '')
            if carrier:
                print(f"    📡 Carrier:      {carrier}")
        else:
            print(f"    🃏 SIM:          Not detected")
        
        # Signal strength
        signal = modem.get('signal', {})
        if signal:
            rssi = signal.get('rssi', 0)
            rsrp = signal.get('rsrp', 0)
            print(f"    📶 Signal RSSI:  {rssi} dBm")
            if rsrp:
                print(f"    📶 Signal RSRP:  {rsrp} dBm")
        
        # Connection info
        connection = modem.get('connection', {})
        if connection:
            imsi = connection.get('imsi', '')
            if imsi:
                # Show only last 4 digits for privacy
                imsi_masked = '*' * (len(imsi) - 4) + imsi[-4:]
                print(f"    🔐 IMSI:         {imsi_masked}")
            
            imei = connection.get('imei', '')
            if imei:
                print(f"    📊 IMEI:         {imei}")
        
        print()

def format_uptime(seconds):
    """Format uptime in human readable format."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def format_bandwidth(bps):
    """Format bandwidth in human readable format (bytes/sec)."""
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps/1024:.1f} KB/s"
    else:
        return f"{bps/(1024*1024):.1f} MB/s"

def main():
    parser = argparse.ArgumentParser(description="GL.inet Router Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Config command
    subparsers.add_parser('config', help='Configure router connection')
    
    # Clients command
    clients_parser = subparsers.add_parser('clients', help='List connected clients')
    clients_parser.set_defaults(handler=lambda r, a: cmd_clients(r, a))
    
    # Block command
    block_parser = subparsers.add_parser('block', help='Block a client')
    block_parser.add_argument('mac', nargs='?', help='MAC address of client to block')
    block_parser.set_defaults(handler=lambda r, a: (setattr(a, 'command', 'block'), cmd_block(r, a)) or None)
    
    # Unblock command
    unblock_parser = subparsers.add_parser('unblock', help='Unblock a client')
    unblock_parser.add_argument('mac', nargs='?', help='MAC address of client to unblock')
    unblock_parser.set_defaults(handler=lambda r, a: (setattr(a, 'command', 'unblock'), cmd_block(r, a)) or None)
    
    # Reboot command
    reboot_parser = subparsers.add_parser('reboot', help='Reboot the router')
    reboot_parser.add_argument('--schedule', help='Schedule reboot at HH:MM (24-hour format)')
    reboot_parser.set_defaults(handler=lambda r, a: cmd_reboot(r, a))
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show router status')
    status_parser.add_argument('what', nargs='?', choices=['system', 'modem', 'all'], default='all',
                               help='What status to show')
    status_parser.set_defaults(handler=lambda r, a: cmd_status(r, a))
    
    args = parser.parse_args()
    
    if args.command == 'config':
        do_config()
    elif args.command:
        try:
            router = get_router()
            args.handler(router, args)
            router.logout()
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
