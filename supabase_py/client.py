from typing import Optional

DEFAULT_OPTIONS = {
    "schema": "public",
    "auto_refresh_token": True,
    "persist_session": True,
    "detect_session_in_url": True,
    "headers": {},
}


class SupabaseClient:
    """
    creates a new client for use in the browser
    """

    def __init__(self, supabase_url, supabase_key, options: Optional[dict] = None):
        """
        :param str supabase_url: The unique Supabase URL which is supplied when you create a new project in your
        project dashboard.
        :param str supabase_key: The unique Supabase Key which is supplied when you create a new project in your project
         dashboard.
        :param dict options: a dictionary of various config for Supabase
        """

        if not supabase_url:
            raise Exception("supabase_url is required")
        if not supabase_key:
            raise Exception("supabase_key is required")

        settings = {**DEFAULT_OPTIONS, **options}
        self.rest_url = f"{supabase_url}/rest/v1"
        self.schema = settings["schema"]
