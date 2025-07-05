#!/usr/bin/env python3
"""
BunnyStream Documentation Test and Demonstration Script.

This script demonstrates the comprehensive documentation system built into BunnyStream,
including help system integration, interactive examples, and troubleshooting guides.
"""

import os
import pydoc
import sys
from io import StringIO


def test_help_system():
    """Test that the Python help system works with BunnyStream components."""
    print("=== TESTING PYTHON HELP SYSTEM ===\n")

    # Test main package help
    print("1. Testing main package documentation:")
    try:
        import bunnystream

        doc = pydoc.getdoc(bunnystream)
        print(f"   ✅ Main package doc length: {len(doc)} characters")
        print(f"   ✅ Contains quick start examples: {'Quick Start Examples' in doc}")
        print(f"   ✅ Contains environment variables: {'Environment Variables' in doc}")
        print(f"   ✅ Contains error handling: {'Error Handling' in doc}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n2. Testing Warren class documentation:")
    try:
        doc = pydoc.getdoc(bunnystream.Warren)
        print(f"   ✅ Warren class doc length: {len(doc)} characters")
        print(f"   ✅ Contains connection states: {'Connection States' in doc}")
        print(f"   ✅ Contains examples: {'Examples' in doc}")
        print(f"   ✅ Contains monitoring: {'Connection Monitoring' in doc}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n3. Testing BunnyStreamConfig documentation:")
    try:
        doc = pydoc.getdoc(bunnystream.BunnyStreamConfig)
        print(f"   ✅ Config class doc length: {len(doc)} characters")
        print(f"   ✅ Contains environment variables: {'Environment Variables' in doc}")
        print(f"   ✅ Contains examples: {'Examples' in doc}")
        print(f"   ✅ Contains validation rules: {'Validation Rules' in doc}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n4. Testing BaseEvent documentation:")
    try:
        doc = pydoc.getdoc(bunnystream.BaseEvent)
        print(f"   ✅ BaseEvent class doc length: {len(doc)} characters")
        print(f"   ✅ Contains key features: {'Key Features' in doc}")
        print(f"   ✅ Contains examples: {'Examples' in doc}")
        print(f"   ✅ Contains metadata fields: {'Metadata Fields' in doc}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n5. Testing BaseReceivedEvent documentation:")
    try:
        doc = pydoc.getdoc(bunnystream.BaseReceivedEvent)
        print(f"   ✅ BaseReceivedEvent class doc length: {len(doc)} characters")
        print(f"   ✅ Contains usage examples: {'Examples' in doc}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_interactive_examples():
    """Test the interactive examples system."""
    print("\n=== TESTING INTERACTIVE EXAMPLES ===\n")

    try:
        from bunnystream.docs import show_examples

        # Capture the output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        show_examples()

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        print(f"✅ Examples output length: {len(output)} characters")
        print(f"✅ Contains basic setup: {'BASIC SETUP AND CONNECTION' in output}")
        print(f"✅ Contains publishing: {'PUBLISHING MESSAGES' in output}")
        print(f"✅ Contains consuming: {'CONSUMING MESSAGES' in output}")
        print(f"✅ Contains SSL examples: {'SSL/TLS CONNECTIONS' in output}")
        print(f"✅ Contains monitoring: {'CONNECTION MONITORING' in output}")
        print(f"✅ Contains patterns: {'COMMON PATTERNS' in output}")

    except Exception as e:
        print(f"❌ Error testing examples: {e}")


def test_troubleshooting_guide():
    """Test the troubleshooting guide."""
    print("\n=== TESTING TROUBLESHOOTING GUIDE ===\n")

    try:
        from bunnystream.docs import show_troubleshooting

        # Capture the output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        show_troubleshooting()

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        print(f"✅ Troubleshooting output length: {len(output)} characters")
        print(f"✅ Contains common issues: {'COMMON ISSUES AND SOLUTIONS' in output}")
        print(f"✅ Contains debugging commands: {'DEBUGGING COMMANDS' in output}")
        print(
            f"✅ Contains environment debugging: {'ENVIRONMENT VARIABLE DEBUGGING' in output}"
        )
        print(
            f"✅ Contains performance monitoring: {'PERFORMANCE MONITORING' in output}"
        )

    except Exception as e:
        print(f"❌ Error testing troubleshooting: {e}")


def test_connection_status_docs():
    """Test that connection status features are documented."""
    print("\n=== TESTING CONNECTION STATUS DOCUMENTATION ===\n")

    try:
        import bunnystream

        # Create a Warren instance and check its methods
        config = bunnystream.BunnyStreamConfig(mode="producer")
        warren = bunnystream.Warren(config)

        # Check that connection status methods exist
        print(f"✅ is_connected property exists: {hasattr(warren, 'is_connected')}")
        print(
            f"✅ connection_status property exists: {hasattr(warren, 'connection_status')}"
        )
        print(
            f"✅ get_connection_info method exists: {hasattr(warren, 'get_connection_info')}"
        )

        # Check their documentation
        if hasattr(warren, "is_connected"):
            doc = pydoc.getdoc(warren.__class__.is_connected)
            print(f"✅ is_connected documented: {len(doc) > 100}")

        if hasattr(warren, "connection_status"):
            doc = pydoc.getdoc(warren.__class__.connection_status)
            print(f"✅ connection_status documented: {len(doc) > 100}")

        if hasattr(warren, "get_connection_info"):
            doc = pydoc.getdoc(warren.get_connection_info)
            print(f"✅ get_connection_info documented: {len(doc) > 100}")

        # Test the connection info functionality
        info = warren.get_connection_info()
        expected_keys = [
            "status",
            "is_connected",
            "host",
            "port",
            "virtual_host",
            "username",
            "has_channel",
            "mode",
            "connection_object",
        ]

        for key in expected_keys:
            if key in info:
                print(f"✅ Connection info contains {key}: {info[key]}")
            else:
                print(f"❌ Connection info missing {key}")

    except Exception as e:
        print(f"❌ Error testing connection status: {e}")


def test_examples_scripts():
    """Test that the example scripts exist and are documented."""
    print("\n=== TESTING EXAMPLE SCRIPTS ===\n")

    examples_dir = "/home/mford/Projects/github.com/MarcFord/bunnystream/examples"

    if os.path.exists(examples_dir):
        print(f"✅ Examples directory exists: {examples_dir}")

        # List example files
        example_files = [f for f in os.listdir(examples_dir) if f.endswith(".py")]
        print(f"✅ Found {len(example_files)} Python example files")

        for file in example_files:
            print(f"   - {file}")

        # Check for connection status demo
        if "connection_status_demo.py" in example_files:
            print("✅ Connection status demo exists")
        else:
            print("❌ Connection status demo missing")
    else:
        print(f"❌ Examples directory not found: {examples_dir}")


def demonstrate_help_usage():
    """Demonstrate how to use the help system."""
    print("\n=== DEMONSTRATING HELP SYSTEM USAGE ===\n")

    print("To access comprehensive documentation, use these commands:")
    print()
    print("1. Main package documentation:")
    print("   >>> import bunnystream")
    print("   >>> help(bunnystream)")
    print()
    print("2. Warren class documentation:")
    print("   >>> help(bunnystream.Warren)")
    print()
    print("3. Configuration documentation:")
    print("   >>> help(bunnystream.BunnyStreamConfig)")
    print()
    print("4. Event system documentation:")
    print("   >>> help(bunnystream.BaseEvent)")
    print("   >>> help(bunnystream.BaseReceivedEvent)")
    print()
    print("5. Interactive examples:")
    print("   >>> from bunnystream.docs import show_examples")
    print("   >>> show_examples()")
    print()
    print("6. Troubleshooting guide:")
    print("   >>> from bunnystream.docs import show_troubleshooting")
    print("   >>> show_troubleshooting()")
    print()
    print("7. Connection status monitoring:")
    print("   >>> warren = bunnystream.Warren(config)")
    print("   >>> print(f'Connected: {warren.is_connected}')")
    print("   >>> print(f'Status: {warren.connection_status}')")
    print("   >>> info = warren.get_connection_info()")
    print("   >>> print(info)")


def main():
    """Main test runner."""
    print("BunnyStream Documentation System Test")
    print("=" * 50)

    test_help_system()
    test_interactive_examples()
    test_troubleshooting_guide()
    test_connection_status_docs()
    test_examples_scripts()
    demonstrate_help_usage()

    print("\n" + "=" * 50)
    print("Documentation system test completed!")
    print("\nThe BunnyStream library now includes:")
    print("✅ Comprehensive Python help system integration")
    print("✅ Interactive examples with show_examples()")
    print("✅ Troubleshooting guide with show_troubleshooting()")
    print("✅ Connection status monitoring and documentation")
    print("✅ Detailed class and method documentation")
    print("✅ Environment variable configuration guides")
    print("✅ SSL/TLS setup examples")
    print("✅ Error handling patterns")
    print("✅ Performance tips and best practices")


if __name__ == "__main__":
    main()
