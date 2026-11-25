# Supabase schema

This directory holds the canonical Supabase database migrations for the optional DuckOS ecosystem control plane.

No hosted project is configured yet. Do not apply these migrations to production until a project has been explicitly provisioned and the migration has passed local database and pgTAP checks.

## Local validation

1. Install the Supabase CLI and Docker using the official instructions.
2. Run `supabase init` in this repository to generate the CLI configuration; preserve the existing migration directory.
3. Start the local stack with `supabase start`.
4. Apply migrations to the local database and run database tests with `supabase test db`.
5. Test that two authenticated users cannot read, update or delete each other's installations or checkpoints, and that anonymous requests cannot access either table.

Before exposing the `public` schema through the Data API, verify the project's Exposed Schemas setting, grants and RLS policies together. Never place service-role or secret keys in this repository or in a client build.

The current migration stores only user-owned installation metadata and opaque sync cursors. Application payloads remain in their local owning repositories.
