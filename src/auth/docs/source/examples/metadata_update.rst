Updating User Metadata
======================

This example demonstrates how to update a user's `app_metadata` and `user_metadata` using the `auth.update_user()` method.

Both `app_metadata` and `user_metadata` accept dictionary/JSON objects, allowing you to store structured custom data for each user.

Example
-------

.. code-block:: python

    import os
    from supabase import create_client, Client

    # Initialize client
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    def update_user_metadata():
        # Metadata fields accept dictionaries/JSON
        new_app_metadata = {
            "plan": "premium",
            "tier": 2
        }

        new_user_metadata = {
            "theme": "dark",
            "language": "en"
        }

        try:
            # Update the currently authenticated user
            response = supabase.auth.update_user({
                "app_metadata": new_app_metadata,
                "user_metadata": new_user_metadata,
            })
            print("Successfully updated metadata.")
        except Exception as e:
            print(f"Error: {e}")

    if __name__ == "__main__":
        update_user_metadata()
