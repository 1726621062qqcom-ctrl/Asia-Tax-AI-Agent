# Taxora Authentication Emails

Status: the user has manually configured Gmail SMTP and the English templates and reported that the actual email workflow works. The agent has not directly inspected the cloud templates to verify them. Later changes to these files will not automatically update Supabase emails.

In the project's Supabase Dashboard, open the Authentication email template settings, copy each entire HTML file into the corresponding template, and save its subject:

| Template | File | Subject |
| --- | --- | --- |
| Confirm sign up | confirm-signup.html | Taxora — Confirm your email |
| Reset password | reset-password.html | Taxora — Reset your password |

Keep `{{ .ConfirmationURL }}`; do not replace it with a local URL or fixed link. The existing frontend relies on the standard verification callback and has not been changed to OTP or PKCE.

The templates use inline styles, table layouts, and text branding, with no external images, domains, scripts, or web fonts. All emails are in English and do not automatically follow the frontend language selection. The templates change only the body and subject; set the sender name to Taxora in SMTP Settings. The dashboard requires custom SMTP configuration before templates can be edited.

Back up existing templates before saving. After saving, use your own test account to verify sign-up, password recovery, expired-link messages, and display in a mobile email client. Do not store real verification links in the repository.

The HTML was written independently using variable conventions from the official Supabase repository and documentation, without copying third-party designs or adding dependencies:

- https://github.com/supabase/auth/blob/master/internal/mailer/templatemailer/templatemailer.go
- https://supabase.com/docs/guides/auth/auth-email-templates
- https://supabase.com/docs/guides/local-development/customizing-email-templates
