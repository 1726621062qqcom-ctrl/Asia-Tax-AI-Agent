<a id="taxora-税衡-邮箱账号与云端数据"></a>

# Taxora Email Accounts and Cloud Data

The product name has been updated to Taxora, using the approved T-shaped logo. Sign-in, registration, password recovery, setting a new password, Chinese/English interfaces, and mobile layouts are integrated. Internal package names and compatibility request headers temporarily retain the old names.

<a id="本机配置"></a>

## Local configuration

Set the following in the project's `.env` (do not commit it):

```dotenv
FSIE_AUTH_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
FSIE_AUTH_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_OR_ANON_KEY
FSIE_AUTH_SITE_URL=http://127.0.0.1:8000
FSIE_AUTH_SECURE_COOKIE=false
```

Obtain the Project URL and Publishable key from Connect or Settings / API Keys in the project dashboard; older projects may use the anon key. Do not use a service_role or secret key. Supabase Auth manages passwords; the application database does not store them.

Supabase Authentication configuration:

1. Enable Email sign-in and email confirmation.
2. Set Site URL under URL Configuration to `http://127.0.0.1:8000`.
3. Add `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/?reset=1` to Redirect URLs.
4. Retain ConfirmationURL in the standard email templates. This version's callback receives the token fragment from the default email flow, immediately removes it from the address bar, and sends it to the backend for validation. Arbitrary custom OTP/PKCE templates are not supported.
5. Configure Custom SMTP before sending registration or reset emails to the team. The default sending service limits recipients and frequency. Verify delivery with an actual mailbox; a success message on the page does not establish email acceptance.

If development port 5173 is used, configure it consistently as the actual application address to prevent authentication callbacks from landing on another origin. For HTTPS deployment, set `FSIE_AUTH_SECURE_COOKIE=true` and configure the deployment domain, callback allowlist, and API TrustedHost. The current startup script binds only to the local machine.

<a id="用户数据如何保存"></a>

## How user data is stored

- The browser calls Supabase Auth through the same-origin backend. Access/refresh tokens are stored in HttpOnly, SameSite=Lax cookies, not localStorage. Sign-in responses do not return tokens.
- The backend validates identity against the configured Supabase project. Only users with confirmed email addresses can access case, retrieval, and analysis APIs. Every read or write uses the server-determined `user:<UUID>` as owner; client-submitted owners are not accepted.
- The existing `chat_cases` table needs no structural changes. New cases are saved to the existing cloud database. Signing into the same account from another browser gives access to the same case collection.
- Cases owned by old browser cookies remain unchanged and are not automatically assigned to any account. Any later migration requires separate confirmation of ownership.
- On sign-out, the frontend unmounts the workspace, clears cases and drafts from memory, and notifies other same-origin tabs to reload. Password reset and sign-in do not automatically grant professional review permissions.
- The server database account remains trusted. This round implements account isolation in the backend; it does not establish database least privilege, organization collaboration, or L1 data approval.

<a id="验证"></a>

## Validation

2026-09-29 update: after an expired email callback clears the token fragment and reset parameter, authentication configuration is still checked and return to sign-in is allowed. The post-registration inbox page, unverified-email sign-in notice, and expired-link notice all provide access to the resend verification flow. `POST /api/auth/resend` accepts only an email address and always uses the signup type and server-configured redirect URL. Nonexistent and already-verified accounts receive the same notice. The frontend provides a 60-second countdown; Supabase enforces server-side rate limits. Actionable notices are retained for 429 responses and sending-service failures. The countdown is interface throttling, not proof of SMTP delivery or expiration of the server-side rate limit.

Offline tests cover identity validation, rejection of unauthenticated access, cross-account read/write isolation, persistence for the same account, password validation, refresh, and sign-out. Browser tests use isolated data and authentication substitutes to cover pages, email notices, recovery callbacks, mobile layouts, and the existing chat flow; they do not establish actual email delivery acceptance.

The live cloud script `scripts/verify_cloud_chat.py` now requires process environment variables `TAXORA_SMOKE_EMAIL` and `TAXORA_SMOKE_PASSWORD` for a verified, dedicated test account. It creates only synthetic cases and cleans up only cases it created. Credentials must not be written to test files.

Use the local `/api/auth/session` endpoint to determine whether the current configuration works. Missing credentials produce a configuration notice rather than anonymous sign-in fallback.

<a id="官方参考"></a>

## Official references

- [Supabase email/password authentication](https://supabase.com/docs/guides/auth/passwords)
- [Identity validation](https://supabase.com/docs/reference/javascript/auth-getuser)
- [Email configuration](https://supabase.com/docs/guides/auth/auth-smtp)

Authentication uses the Supabase HTTP API and retains the existing FastAPI same-origin interfaces, without adding a browser authentication SDK. The implementation draws on official code and recent session-refresh fixes; no third-party UI or code was copied.
