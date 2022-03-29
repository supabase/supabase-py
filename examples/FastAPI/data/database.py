# variables for database and url configuration
from config import Config

from supabase import Client, create_client


class SupabaseDB:
    """
    class instance for database connection to supabase

    :str: url: configuration for database url for data inside supafast project
    :str: key: configuration for database secret key for authentication
    :object: supabase: Supabase instance for connection to database environment
    """

    url: str = Config.URL
    key: str = Config.KEY
    supabase: Client = create_client(url, key)
