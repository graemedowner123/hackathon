#!/usr/bin/env python3
"""
Check the status of the bot bidding system
"""

import os
import sys
import requests
import json
from datetime import datetime

def check_bot_status():
    """Check if the bot system is running"""
    print("🔍 Checking Bot Bidding System Status")
    print("=" * 40)
    
    # Check if Flask app is running
    try:
        response = requests.get('http://localhost:5000/admin/bots/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Flask application is running")
            print("✅ Bot system is accessible")
            
            print(f"\n📊 Bot Statistics:")
            print(f"   Total Bots: {stats.get('total_bots', 0)}")
            print(f"   Total Capital: ${stats.get('total_capital', 0):,.2f}")
            print(f"   Available Capital: ${stats.get('available_capital', 0):,.2f}")
            print(f"   Active Bids: {stats.get('active_bids', 0)}")
            print(f"   Funded Loans: {stats.get('funded_loans', 0)}")
            
            if stats.get('bots'):
                print(f"\n🤖 Individual Bot Status:")
                for bot in stats['bots']:
                    utilization = bot.get('utilization', 0)
                    print(f"   • {bot['name']}: {utilization:.1f}% utilized, "
                          f"{bot['active_bids']} active bids")
            
            return True
            
        else:
            print(f"❌ Flask app responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Flask application is not running")
        print("   Start it with: python3 app_dynamodb.py")
        return False
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def check_processes():
    """Check for running Python processes"""
    print(f"\n🔍 Checking Running Processes:")
    
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        python_processes = []
        for line in result.stdout.split('\n'):
            if 'python' in line.lower() and ('app_dynamodb' in line or 'start_bots' in line):
                python_processes.append(line.strip())
        
        if python_processes:
            print("✅ Found Python processes:")
            for process in python_processes:
                print(f"   {process}")
        else:
            print("❌ No relevant Python processes found")
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")

def check_log_files():
    """Check for log files"""
    print(f"\n📄 Checking Log Files:")
    
    log_files = ['bot_bidding.log', 'app.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                stat = os.stat(log_file)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
                print(f"✅ {log_file}: {size} bytes, modified {modified}")
                
                # Show last few lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"   Last entry: {lines[-1].strip()}")
                        
            except Exception as e:
                print(f"❌ Error reading {log_file}: {e}")
        else:
            print(f"❌ {log_file}: Not found")

def main():
    """Main status check function"""
    print(f"Bot System Status Check - {datetime.now()}")
    print("=" * 50)
    
    # Check bot system status
    bot_running = check_bot_status()
    
    # Check processes
    check_processes()
    
    # Check log files
    check_log_files()
    
    print(f"\n📋 Summary:")
    if bot_running:
        print("✅ Bot bidding system is operational")
        print("   Bots are ready to evaluate and bid on loan requests")
    else:
        print("❌ Bot bidding system is not running")
        print("   To start: python3 start_bots.py")
        print("   Or demo: python3 demo_bots.py")
    
    print(f"\n💡 Quick Commands:")
    print(f"   Demo mode: python3 demo_bots.py")
    print(f"   Start bots: python3 start_bots.py")
    print(f"   Test system: python3 test_bots.py")
    print(f"   View guide: cat AGENT_BIDDING_GUIDE.md")

if __name__ == "__main__":
    main()
