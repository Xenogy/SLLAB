#!/usr/bin/env python3
"""
Password Hash Generator

This script generates a Bcrypt password hash compatible with the AccountDB system.
It uses the same hashing method as the application.
"""

from passlib.context import CryptContext
import argparse
import getpass

# Create the same password context as in the application
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Generate a password hash using Bcrypt."""
    return pwd_context.hash(password)

def main():
    parser = argparse.ArgumentParser(description='Generate a Bcrypt password hash.')
    parser.add_argument('-p', '--password', help='Password to hash (if not provided, will prompt securely)')
    parser.add_argument('-v', '--verify', help='Verify a password against a hash')
    args = parser.parse_args()

    if args.verify:
        # Verify mode
        password = args.password
        if not password:
            password = getpass.getpass('Enter password to verify: ')
        
        hash_to_verify = args.verify
        result = pwd_context.verify(password, hash_to_verify)
        
        if result:
            print("\n✅ Password verification successful!")
        else:
            print("\n❌ Password verification failed!")
        
        return

    # Hash generation mode
    password = args.password
    if not password:
        # Prompt for password if not provided as argument (more secure)
        password = getpass.getpass('Enter password to hash: ')
        confirm = getpass.getpass('Confirm password: ')
        
        if password != confirm:
            print("Passwords do not match!")
            return
    
    # Generate the hash
    hashed_password = get_password_hash(password)
    
    print("\nGenerated Password Hash:")
    print(f"{hashed_password}")
    print("\nThis hash can be used directly in the users table of your database.")
    print("Format: $2b$12$[salt+hash] (Bcrypt with work factor 12)")

if __name__ == "__main__":
    main()
