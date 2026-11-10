# Contributing to OpenTrace

We welcome community contributions to expand platform coverage and improve detection accuracy.

## Adding a New Platform Definition
To add a new platform:
1. Open `packages/site-registry/registry.py`.
2. Add a new `SiteDefinition` specifying:
   - `name`: Human-readable platform name.
   - `category`: `PlatformCategory` enum value.
   - `url_pattern`: Profile URL pattern containing `{username}`.
   - `check_type`: `DetectionMethod` (e.g. `COMPOSITE`, `JSON_API`).
   - `absence_indicators`: Strings or soft-404 markers proving the user does not exist.
   - `presence_indicators`: Strings proving the profile page is genuine.
   - `extract_*_regex`: Optional extraction rules for display name, bio, avatar, and website.
3. Run the test suite:
   ```bash
   make test
   ```
4. Verify with a live probe test:
   ```bash
   make test-live
   ```

