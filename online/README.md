# Project C3 Web v0.10 — closed online alpha

Status: staged, NOT deployed. Keep the existing v0.9.1 single-player Pages release working.

## Activation
1. Create a dedicated Supabase project. Configure email/password Auth, email verification, and the site/redirect URL https://dribendriben-byte.github.io/ProjectC3-Web/.
2. Apply schema.sql in that project. Never put a service-role/secret key into GitHub or the browser.
3. Register the owner account through Auth. Grant GM via the SQL editor with the exact registered user UUID: insert into public.c3_gms(user_id) values ('OWNER_UUID'); Do not allow self-assignment from a browser.
4. Add a browser configuration containing only the project URL and publishable (anon) key, e.g. window.C3_CONFIG={url:"https://PROJECT.supabase.co",key:"PUBLISHABLE_KEY"}; save as online/config.js.
5. After the existing 0.9.1 patch, run python3 online/integrate.py source/ProjectC3_Web_v0.9/Ford3D. After Godot export, copy online/bridge.js to site/c3-online.js and online/config.js to site/c3-config.js. Use a separate preview first and validate compilation before deploying over the live version.
6. Test two distinct accounts in different devices/incognito sessions. Verify own save restores, unauthorized GM requests fail, character bans work, guest saves stay separate, and two players see one another. Test errors, disconnect/reconnect, duplicate names, refresh and map transitions.

## Scope and caveats
- One character per account for this milestone. Race and class use existing game definitions; gender and appearance are stored, visual models still need work.
- Shared presence and interpolated remote avatars only; mobs, XP, loot, combat and economy remain client-side. Treat saves as untrusted private-alpha data. Not a production MMORPG or proof of 1,000 concurrent users.
- GM panel lists characters/progress/online status and can ban/unban with audit records. No public service-role key. No economy adjustments until authoritative server implementation.
- Periodic cloud saves, but abrupt close/network failure can lose recent progress; two sessions for the same account may overwrite one another. Add session locking and revision checks before open testing.
- Before opening registration to the public, add rate limits/abuse protections, custom SMTP as needed, authoritative world simulation and tests. Current presence polling is not designed for large-scale concurrency.
- Schedule independent encrypted Postgres backups including Auth data using supported export tools; store separately from Supabase, test restoration, and never commit dumps to the public repo. Free-plan backups are not guaranteed. No backup scheduler is configured yet.
