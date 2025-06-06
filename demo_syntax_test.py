#!/usr/bin/env python3
"""
Demo Python file to showcase syntax highlighting improvements.
This file contains various Python syntax elements to test highlighting.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union

# Global constants
VERSION = "1.0.0"
DEFAULT_CONFIG = {
    "debug": True,
    "max_items": 100,
    "timeout": 30.5
}


class SyntaxHighlightDemo:
    """A demo class showcasing various Python syntax elements."""
    
    def __init__(self, name: str, items: List[str] = None):
        """Initialize the demo with a name and optional items."""
        self.name = name
        self.items = items or []
        self._private_count = 0
    
    @property 
    def count(self) -> int:
        """Get the current count."""
        return self._private_count
    
    @staticmethod
    def create_greeting(name: str) -> str:
        """Create a personalized greeting."""
        if not name:
            return "Hello, Anonymous!"
        return f"Hello, {name.title()}! 👋"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, List]]) -> 'SyntaxHighlightDemo':
        """Create instance from dictionary."""
        return cls(
            name=data.get('name', 'Unknown'),
            items=data.get('items', [])
        )
    
    def process_items(self, filter_func=None) -> List[str]:
        """Process items with optional filtering."""
        result = []
        
        for i, item in enumerate(self.items):
            # This is a comment explaining the logic
            if filter_func and not filter_func(item):
                continue
                
            # Multi-line string with f-string
            processed = f"""
            Item {i}: {item.upper()}
            Length: {len(item)}
            Type: {type(item).__name__}
            """
            
            result.append(processed.strip())
            self._private_count += 1
        
        return result
    
    def __str__(self) -> str:
        """String representation."""
        return f"SyntaxHighlightDemo(name='{self.name}', items={len(self.items)})"
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"SyntaxHighlightDemo({self.name!r}, {self.items!r})"


def main():
    """Main function demonstrating the syntax highlighting."""
    # Create demo instance
    demo = SyntaxHighlightDemo("Test Demo", ["apple", "banana", "cherry"])
    
    # Lambda function
    vowel_filter = lambda x: x[0].lower() in 'aeiou'
    
    # List comprehension with conditional
    filtered_items = [item for item in demo.items if len(item) > 4]
    
    # Dictionary comprehension
    item_lengths = {item: len(item) for item in demo.items}
    
    # Set comprehension
    unique_lengths = {len(item) for item in demo.items}
    
    # Generator expression
    capitalized = (item.upper() for item in demo.items)
    
    # Exception handling
    try:
        result = demo.process_items(vowel_filter)
        print("✅ Processing successful!")
        
        # Nested loops with enumerate
        for i, processed_item in enumerate(result):
            print(f"  {i + 1}. {processed_item}")
            
    except (ValueError, TypeError) as e:
        print(f"❌ Error during processing: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        print(f"🔄 Total processed: {demo.count}")
    
    # Context manager
    with Path("test.txt").open("w") as f:
        f.write("Demo file content\n")
    
    # Format strings
    summary = f"""
    Demo Summary:
    =============
    Name: {demo.name}
    Items: {demo.items}
    Lengths: {item_lengths}
    Unique lengths: {unique_lengths}
    Greeting: {demo.create_greeting("Developer")}
    """
    
    print(summary)
    
    # Multiple assignment
    a, b, c = 1, 2, 3
    
    # Walrus operator (Python 3.8+)
    if (n := len(demo.items)) > 2:
        print(f"We have {n} items!")
    
    # Return multiple values
    return demo, result, item_lengths


# Module-level execution
if __name__ == "__main__":
    print("🚀 Starting Syntax Highlighting Demo...")
    print("=" * 50)
    
    # Call main function
    demo_obj, results, lengths = main()
    
    print("\n" + "=" * 50)
    print("✨ Demo completed successfully!")
    print(f"📊 Final object: {demo_obj}") 