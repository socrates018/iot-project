import paramiko
import argparse
import json
import os
import sys
from typing import Dict, List

def load_configuration(config_path: str) -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        required_keys = ['hostname', 'username', 'password', 'commands']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required key in config: {key}")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def execute_ssh_commands(config: Dict) -> None:
    """Execute commands over SSH with automatic password handling"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Establish SSH connection
        client.connect(
            hostname=config['hostname'],
            username=config['username'],
            password=config['password'],
            timeout=10
        )
        print(f"Connected to {config['hostname']} successfully!")

        # Execute each command
        for cmd in config['commands']:
            print(f"\nExecuting: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            # Print command output
            output = stdout.read().decode().strip()
            errors = stderr.read().decode().strip()
            
            if output:
                print("Output:\n", output)
            if errors:
                print("Errors:\n", errors)
            print(f"Exit Status: {exit_status}")

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check credentials.")
    except paramiko.SSHException as e:
        print(f"SSH connection failed: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("\nConnection closed.")

def main():
    parser = argparse.ArgumentParser(
        description="Automated SSH Command Executor for Raspberry Pi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-c', '--config', default='config.json',
                      help="Path to configuration file")
    parser.add_argument('-H', '--hostname', help="Raspberry Pi IP/hostname")
    parser.add_argument('-u', '--username', help="SSH username")
    parser.add_argument('-p', '--password', help="SSH password")
    parser.add_argument('-cmds', '--commands', nargs='+', 
                      help="List of commands to execute")

    args = parser.parse_args()

    # Configuration priority: command-line args > config file
    if os.path.exists(args.config):
        config = load_configuration(args.config)
    else:
        config = {}

    # Override config with command-line arguments
    if args.hostname: config['hostname'] = args.hostname
    if args.username: config['username'] = args.username
    if args.password: config['password'] = args.password
    if args.commands: config['commands'] = args.commands

    # Validate final configuration
    required_keys = ['hostname', 'username', 'password', 'commands']
    for key in required_keys:
        if key not in config:
            print(f"Missing required parameter: {key}")
            sys.exit(1)

    execute_ssh_commands(config)

if __name__ == "__main__":
    main()