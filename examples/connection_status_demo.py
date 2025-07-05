#!/usr/bin/env python3
"""
Connection Status Demo for BunnyStream Warren

This example demonstrates how to use the new connection status functionality
in the Warren class to monitor RabbitMQ connection status.
"""

from bunnystream.config import BunnyStreamConfig
from bunnystream.warren import Warren


def main():
    """Demonstrate connection status functionality."""
    # Create a configuration
    config = BunnyStreamConfig(mode="producer")

    # Create Warren instance
    warren = Warren(config)

    # Check initial connection status
    print("=== Initial Connection Status ===")
    print(f"Is connected: {warren.is_connected}")
    print(f"Connection status: {warren.connection_status}")
    print()

    # Get detailed connection info
    print("=== Detailed Connection Info ===")
    info = warren.get_connection_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    print()

    # Simulate connecting (this would normally connect to RabbitMQ)
    print("=== Simulating Connection ===")
    print("Note: This would normally connect to RabbitMQ")
    print("To actually connect, you need a running RabbitMQ server")
    print("Example: warren.connect(); warren.start_io_loop()")
    print()

    # Show what the status would look like when connected
    print("=== Example: Connected Status ===")
    print("When connected to RabbitMQ:")
    print("- warren.is_connected would return: True")
    print("- warren.connection_status would return: 'connected'")
    print("- warren.get_connection_info() would show connection details")

    # Demonstrate status checking in a monitoring loop
    print("\n=== Connection Monitoring Example ===")
    print("Example monitoring loop:")
    print("""
def monitor_connection(warren):
    while True:
        status = warren.connection_status
        if status == "connected":
            print("✅ RabbitMQ connection is healthy")
        elif status == "disconnected":
            print("❌ RabbitMQ connection lost - attempting reconnect")
            # Reconnection logic here
        else:
            print("⏳ RabbitMQ not initialized")
        
        time.sleep(10)  # Check every 10 seconds
    """)


if __name__ == "__main__":
    main()
