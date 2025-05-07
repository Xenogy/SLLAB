import re

# Test string
test_string = "Beginning startup for dissdonk649"

# Regex pattern with named capture group
pattern = r'Beginning startup for (?P<account_id>\w+)'

# Try to match the pattern
match = re.search(pattern, test_string)

if match:
    account_id = match.group('account_id')
    print(f"Extracted account ID: {account_id}")
else:
    print("No match found")
