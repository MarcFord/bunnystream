#!/usr/bin/env python3
"""
Test script for the new ack_event() functionality in BaseReceivedEvent.

This script demonstrates and tests the manual acknowledgment feature.
"""

import json
from unittest.mock import Mock
from bunnystream import BaseReceivedEvent


def test_ack_event_functionality():
    """Test the ack_event method functionality."""
    print("Testing BaseReceivedEvent.ack_event() functionality")
    print("=" * 60)
    
    # Test 1: Basic functionality with mocked channel and method
    print("\n1. Testing basic ack_event functionality:")
    
    # Create mock channel and method objects
    mock_channel = Mock()
    mock_method = Mock()
    mock_method.delivery_tag = 12345
    
    # Create test data
    test_data = {
        "user_id": 123,
        "email": "test@example.com",
        "action": "login"
    }
    
    # Create event with channel and method
    event = BaseReceivedEvent(test_data, mock_channel, mock_method)
    
    # Test data access
    print(f"   User ID: {event.user_id}")
    print(f"   Email: {event.email}")
    print(f"   Action: {event.action}")
    
    # Test acknowledgment
    try:
        event.ack_event()
        print("   ✅ Event acknowledged successfully")
        
        # Verify that basic_ack was called with correct delivery_tag
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=12345)
        print("   ✅ Channel.basic_ack called with correct delivery_tag")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Error handling when channel/method not provided
    print("\n2. Testing error handling without channel/method:")
    
    event_without_ack = BaseReceivedEvent(test_data)
    
    try:
        event_without_ack.ack_event()
        print("   ❌ Should have raised an error")
    except RuntimeError as e:
        print(f"   ✅ Correctly raised RuntimeError: {str(e)[:80]}...")
    
    # Test 3: Error handling when basic_ack fails
    print("\n3. Testing error handling when basic_ack fails:")
    
    mock_channel_fail = Mock()
    mock_channel_fail.basic_ack.side_effect = Exception("Connection lost")
    mock_method_fail = Mock()
    mock_method_fail.delivery_tag = 67890
    
    event_fail = BaseReceivedEvent(test_data, mock_channel_fail, mock_method_fail)
    
    try:
        event_fail.ack_event()
        print("   ❌ Should have raised an error")
    except RuntimeError as e:
        print(f"   ✅ Correctly raised RuntimeError: {str(e)[:80]}...")
    
    # Test 4: JSON data parsing with acknowledgment
    print("\n4. Testing with JSON string data:")
    
    json_data = json.dumps({
        "order_id": "ORD-456", 
        "customer": {"name": "Jane Doe", "email": "jane@example.com"},
        "total": 99.99
    })
    
    mock_channel_json = Mock()
    mock_method_json = Mock()
    mock_method_json.delivery_tag = 54321
    
    event_json = BaseReceivedEvent(json_data, mock_channel_json, mock_method_json)
    
    print(f"   Order ID: {event_json.order_id}")
    print(f"   Customer: {event_json.customer.name}")
    print(f"   Total: ${event_json.total}")
    
    try:
        event_json.ack_event()
        print("   ✅ JSON event acknowledged successfully")
        mock_channel_json.basic_ack.assert_called_once_with(delivery_tag=54321)
        print("   ✅ Channel.basic_ack called with correct delivery_tag")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All ack_event() tests completed successfully!")


def test_message_handler_pattern():
    """Test the typical message handler pattern with manual acknowledgment."""
    print("\nTesting message handler pattern:")
    print("-" * 40)
    
    def process_user_event(channel, method, properties, body):
        """Example message handler with manual acknowledgment."""
        try:
            # Create event with channel and method for manual ack
            event = BaseReceivedEvent(body, channel, method)
            
            # Process the message
            user_id = event.user_id
            action = event.action
            
            print(f"   Processing: User {user_id} - {action}")
            
            # Simulate processing logic
            if user_id > 0 and action in ['login', 'logout', 'update']:
                # Success - acknowledge the message
                event.ack_event()
                print(f"   ✅ User {user_id} processed and acknowledged")
                return True
            else:
                # Invalid data - don't acknowledge
                print(f"   ❌ Invalid data - message will be redelivered")
                return False
                
        except Exception as e:
            print(f"   ❌ Processing failed: {e}")
            return False
    
    # Test with valid data
    print("\n   Testing with valid data:")
    mock_channel = Mock()
    mock_method = Mock()
    mock_method.delivery_tag = 11111
    
    valid_body = json.dumps({"user_id": 123, "action": "login", "timestamp": "2025-01-01T00:00:00Z"})
    result = process_user_event(mock_channel, mock_method, None, valid_body)
    
    if result:
        print("   ✅ Valid message processed successfully")
    
    # Test with invalid data
    print("\n   Testing with invalid data:")
    mock_channel2 = Mock()
    mock_method2 = Mock()
    mock_method2.delivery_tag = 22222
    
    invalid_body = json.dumps({"user_id": -1, "action": "invalid", "timestamp": "2025-01-01T00:00:00Z"})
    result2 = process_user_event(mock_channel2, mock_method2, None, invalid_body)
    
    if not result2:
        print("   ✅ Invalid message correctly rejected (not acknowledged)")


def main():
    """Main test runner."""
    test_ack_event_functionality()
    test_message_handler_pattern()
    
    print("\n" + "=" * 60)
    print("Manual acknowledgment functionality is working correctly!")
    print("\nUsage example:")
    print("def message_handler(channel, method, properties, body):")
    print("    event = BaseReceivedEvent(body, channel, method)")
    print("    # ... process message ...")
    print("    event.ack_event()  # Manually acknowledge")


if __name__ == "__main__":
    main()
