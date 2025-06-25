#!/usr/bin/env python3
"""
Demo script showing RABBITMQ_URL environment variable functionality in bunnystream.

This script demonstrates how the Warren class can automatically parse
RABBITMQ_URL environment variable to configure connection parameters.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bunnystream import Warren


def demo_rabbitmq_url_parsing():
    """Demonstrate RABBITMQ_URL parsing functionality."""

    print("=== BunnyStream RABBITMQ_URL Demo ===\n")

    # 1. Show default behavior (no environment variable)
    print("1. Default behavior (no RABBITMQ_URL):")
    warren1 = Warren(rabbit_host="localhost")
    print(f"   Host: {warren1.rabbit_host}")
    print(f"   Port: {warren1.rabbit_port}")
    print(f"   VHost: {warren1.rabbit_vhost}")
    print(f"   User: {warren1.rabbit_user}")
    print(f"   Pass: {warren1.rabbit_pass}")
    print(f"   URL: {warren1.url}")
    print()

    # 2. Set RABBITMQ_URL and show parsing
    print("2. With RABBITMQ_URL environment variable:")
    os.environ["RABBITMQ_URL"] = "amqp://myuser:mypass@rabbit.example.com:5673/myvhost"

    warren2 = Warren()
    print(f"   RABBITMQ_URL: {os.environ['RABBITMQ_URL']}")
    print(f"   Parsed Host: {warren2.rabbit_host}")
    print(f"   Parsed Port: {warren2.rabbit_port}")
    print(f"   Parsed VHost: {warren2.rabbit_vhost}")
    print(f"   Parsed User: {warren2.rabbit_user}")
    print(f"   Parsed Pass: {warren2.rabbit_pass}")
    print(f"   Generated URL: {warren2.url}")
    print()

    # 3. Show environment variable with URL-encoded characters
    print("3. With URL-encoded special characters:")
    os.environ["RABBITMQ_URL"] = (
        "amqp://user%40domain:p%40ssw0rd@secure.example.com:5671/prod%2Fapp"
    )

    warren3 = Warren()
    print(f"   RABBITMQ_URL: {os.environ['RABBITMQ_URL']}")
    print(f"   Decoded User: {warren3.rabbit_user}")
    print(f"   Decoded Pass: {warren3.rabbit_pass}")
    print(f"   Decoded VHost: {warren3.rabbit_vhost}")
    print()

    # 4. Show constructor parameters override environment
    print("4. Constructor parameters override environment:")
    warren4 = Warren(rabbit_host="override.example.com", rabbit_port=9999)
    print(f"   Environment Host: {os.environ['RABBITMQ_URL'].split('@')[1].split(':')[0]}")
    print(f"   Actual Host: {warren4.rabbit_host} (overridden)")
    print("   Environment Port: 5671")
    print(f"   Actual Port: {warren4.rabbit_port} (overridden)")
    print(f"   User from env: {warren4.rabbit_user} (from environment)")
    print()

    # 5. Show error handling
    print("5. Error handling for invalid URL:")
    try:
        os.environ["RABBITMQ_URL"] = "invalid://bad-url"
        Warren()  # This will raise an error
    except ValueError as e:
        print(f"   Caught expected error: {e}")

    # Clean up
    if "RABBITMQ_URL" in os.environ:
        del os.environ["RABBITMQ_URL"]

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_rabbitmq_url_parsing()
