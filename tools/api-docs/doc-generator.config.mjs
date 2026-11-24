import { defineConfig } from "@supabase/doc-generator";

// Config file for the doc generator. Paths are relative to this file.
//
// See XXX for the format this generator expects of the comments.
//
// Every function and method that can be imported by public names, gets one definition. Its id is its import path in
// lowercase words: `storage3.StorageFileApiClient.upload` becomes `storage3-storage-file-api-client-upload`. 
export default defineConfig({
  // Doc format
  source: {
    format: "griffe", // The generator will run `griffe dump`
    file: "build/griffe.json",
    // A method wrapped by `handle_http_io` is declared once for the sync and the async client and
    // returns `HttpMethod[T]`. A caller gets `T` from the sync client and awaits it on the async one.
    unwrapReturns: ["supabase_utils.http.io.HttpMethod"],
    // How a user reaches the methods of a class, by the import path of the class. A class that is
    // not listed is documented under its import path. This list is a start, not complete.
    symbolPaths: {
      "supabase_auth.SyncSupabaseAuthClient": "supabase.auth",
      "supabase_functions.client.FunctionsClient": "supabase.functions",
      "storage3.client.StorageClient": "supabase.storage",
      "storage3.StorageFileApiClient": "supabase.storage.from_(bucket)",
    },
  },
  output: "../../docs/api-docs/definitions",
  // Not `strict: true` yet: 228 public functions have no docstring. `make api-docs` counts them.
  // Where the docs site shows this SDK: /docs/reference-beta/python. For `make api-docs-preview`.
  preview: { path: "python", title: "Python" },
});
