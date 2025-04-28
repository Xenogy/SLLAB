"""
Simple test script for the password validator.
"""

import sys
import os
from utils.password_validator import validate_password_strength, get_password_strength_feedback

# Test empty password
print("Testing empty password:")
is_strong, score, feedback = validate_password_strength("")
print(f"Is strong: {is_strong}")
print(f"Score: {score}")
print(f"Feedback: {feedback}")
print()

# Test short password
print("Testing short password:")
is_strong, score, feedback = validate_password_strength("abc123")
print(f"Is strong: {is_strong}")
print(f"Score: {score}")
print(f"Feedback: {feedback}")
print()

# Test password without uppercase
print("Testing password without uppercase:")
is_strong, score, feedback = validate_password_strength("abcdefg123!")
print(f"Is strong: {is_strong}")
print(f"Score: {score}")
print(f"Feedback: {feedback}")
print()

# Test strong password
print("Testing strong password:")
is_strong, score, feedback = validate_password_strength("P@ssw0rd!X")
print(f"Is strong: {is_strong}")
print(f"Score: {score}")
print(f"Feedback: {feedback}")
print()
