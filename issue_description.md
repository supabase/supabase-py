# Issue: Custom headers are not preserved when creating Supabase client

## Description
When initializing a Supabase client with custom headers through `ClientOptions`, the custom headers are completely overwritten by the authentication headers instead of being merged with them. This prevents users from setting custom headers such as application identifiers, API version headers, or other metadata needed for their requests.

The bug affects both sync and async client implementations. Custom headers like `x-app-name`, `x-version`, or any other user-defined headers passed via `ClientOptions(headers={...})` are lost during client initialization because the code overwrites the entire headers dictionary with only the auth headers, rather than merging the two sets of headers together.

This also causes issues with header immutability when multiple clients are created with the same `ClientOptions` instance, as modifications to one client's headers could affect others if not properly isolated.

## Example
```python
from supabase import create_client, ClientOptions

options = ClientOptions(
    headers={
        "x-app-name": "my-app",
        "x-version": "1.0",
    }
)

client = create_client(url, key, options)
# Bug: client.options.headers["x-app-name"] returns None instead of "my-app"
```

## Impact
- Users cannot set custom headers for their API requests
- Application-specific headers for monitoring, versioning, or identification are lost
- Potential issues with shared ClientOptions instances between multiple clients

## Original PR Reference
This issue was originally fixed in PR #1155: "fix: custom headers not setting"