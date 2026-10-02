# T2W Elite portal: Supabase notes

Project: "mr2ndwind's Project" (shared with T2W StatLab). Elite objects are prefixed `elite_` or live in
`elite_private` (helper functions, not exposed through the API). StatLab objects are not modified except
the signup trigger described below.

## Account rules
- Public signups OFF. Every account is created by invite from an admin context.
- Elite accounts: `app_metadata.product = "elite"`. StatLab accounts: `app_metadata.product = "statlab"`.
  The signup trigger only creates a StatLab (coach) profile for `product = "statlab"`.
- Elite role/status/verified_at are changed by staff via SQL or service role only. Users can edit display_name.

## Applied migrations (2026-10-02, approved by Corey)
1. harden_statlab_signup_trigger_and_function_grants
2. elite_portal_schema_v1
3. elite_portal_table_grants
4. elite_nil_guardian_status_limit

Tested in rolled-back transactions: parent sees only own athlete; verified recruiter sees only
guardian-approved, recruiter-visible profiles; pending recruiter and anon see nothing; no self role escalation.

## Still manual (dashboard)
- DONE (Corey, 2026-10-02): "Allow new users to sign up" is OFF; password requirements raised
- Leaked password protection is a paid-plan (Pro) feature; not available on the Free plan
- Custom SMTP for elite@t2welite.com: pending DNS verification at GoDaddy (see below)

## Portal pages (this branch)
- `/portal/login/` sign in + Forgot password; `/portal/reset/` set/reset password (also used by invite links);
  `/portal/home/` role-aware, read-only home (parent, athlete, recruiter/school, staff).
- Pages use the public publishable key in `config.json > supabase`. Data access is enforced by row-level security.
- Portal pages are `noindex` and excluded from the sitemap.
- supabase-js loads from jsDelivr (`@supabase/supabase-js@2`). TODO before launch: pin an exact version.

## Before cutover (manual, in Supabase dashboard)
1. Authentication > URL Configuration: set Site URL to https://t2welite.com and add redirect URLs
   https://t2welite.com/portal/reset/ and https://t2welite.com/portal/home/.
2. Authentication > Emails > SMTP Settings: connect the sending service for elite@t2welite.com
   (verify the domain at the DNS host first). Customize the Reset Password and Invite templates.
3. Create a test parent account by invite (app_metadata product=elite), add an elite_profiles row, and
   run the end-to-end check: invite -> set password -> login -> home -> forgot password -> reset.

## Tested
Browser tests with simulated server replies (21 checks: login errors, forgot password, expired link,
redirects, parent/pending/recruiter/no-profile views). NOT yet tested against the live Supabase project
(sandbox cannot reach it) and NOT yet tested with real emails.
