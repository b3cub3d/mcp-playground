import sys
import os

# Add the src directory to the path so we can import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import greet

def test_greet():
    assert greet("World") == "Hello, World!"
    assert greet("Python") == "Hello, Python!" 