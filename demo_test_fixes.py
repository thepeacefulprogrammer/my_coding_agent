#!/usr/bin/env python3
"""
Demo script to test both syntax highlighting and folder navigation fixes
"""

# This file demonstrates various Python syntax elements for testing
import os
import sys
from typing import List, Dict

# Constants with different types
DEMO_VERSION = "2.0.0"
SETTINGS = {
    "theme": "dark",
    "font_size": 12,
    "auto_save": True
}

class DemoCodeHighlighting:
    """Class to showcase syntax highlighting improvements"""
    
    def __init__(self, name: str):
        self.name = name
        self._count = 0
    
    @property
    def count(self) -> int:
        """Get current count"""
        return self._count
    
    def process_data(self, items: List[str]) -> Dict[str, int]:
        """Process items and return statistics"""
        result = {}
        
        for item in items:
            # Comment: processing each item
            if isinstance(item, str) and len(item) > 0:
                result[item] = len(item)
                self._count += 1
            
        return result
    
    def create_summary(self) -> str:
        """Create formatted summary"""
        return f"""
        Demo Summary:
        =============
        Name: {self.name}
        Count: {self._count}
        Settings: {SETTINGS}
        Version: {DEMO_VERSION}
        """

def main():
    """Main function demonstrating syntax elements"""
    # Create demo instance
    demo = DemoCodeHighlighting("Syntax Test")
    
    # Test data
    test_items = ["apple", "banana", "cherry", "date"]
    
    # Process data
    stats = demo.process_data(test_items)
    
    # List comprehension
    long_items = [item for item in test_items if len(item) > 5]
    
    # Dictionary comprehension
    uppercase_stats = {k.upper(): v for k, v in stats.items()}
    
    # Exception handling
    try:
        # File operations
        with open("test.txt", "w") as f:
            f.write("Test file content\n")
        
        print("✅ File created successfully")
        
    except IOError as e:
        print(f"❌ Error: {e}")
    
    finally:
        print(f"🔄 Processing complete: {demo.count} items")
    
    # Lambda and filter
    short_items = list(filter(lambda x: len(x) <= 5, test_items))
    
    # F-string formatting
    summary = f"Processed {len(test_items)} items, found {len(long_items)} long items"
    
    print(summary)
    print(demo.create_summary())
    
    return demo, stats

if __name__ == "__main__":
    print("🚀 Testing Syntax Highlighting Fixes...")
    print("=" * 50)
    
    demo_obj, results = main()
    
    print("\n" + "=" * 50)
    print("✨ Test completed!")
    print(f"Results: {results}") 