import pytest

import sys
print(sys.path)

import supabase_py

def test_dummy():
    # Test auth component
    assert True == True

def test_client_initialziation():
    client = supabase_py.Client("http://testwebsite.com", "atestapi")