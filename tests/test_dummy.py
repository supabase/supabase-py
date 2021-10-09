import supabase

"""
Convert this flow into a test
client = supabase.Client("<insert link>", "<password>")
client.auth.sign_up({"email": "anemail@gmail.com", "password": "apassword"})
"""


def test_dummy() -> None:
    # Test auth component
    assert True == True


def test_client_initialziation() -> None:
    client = supabase.Client("http://testwebsite.com", "atestapi")
