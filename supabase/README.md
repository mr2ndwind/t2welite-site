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
- Turn OFF "Allow new users to sign up"
- Turn ON leaked password protection
- Configure custom SMTP (sender address pending decision)
