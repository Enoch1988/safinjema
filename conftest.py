# conftest.py – pytest configuration for async tests
import os
import pytest

# Must be set BEFORE any app imports
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only_32chars_min")
os.environ.setdefault("SMTP_PASS",  "")           # Disable real emails in tests
os.environ.setdefault("ADMIN_EMAIL",    "admin@test.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminTest123!")
os.environ.setdefault("ADMIN_NAME",     "Test Admin")
os.environ.setdefault("DEBUG", "true")
