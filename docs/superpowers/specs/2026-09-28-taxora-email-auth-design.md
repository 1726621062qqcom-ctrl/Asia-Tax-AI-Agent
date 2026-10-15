<a id="taxora-邮箱登录设计与实施顺序"></a>

# Taxora Email Sign-In Design and Implementation Order

The user confirmed the warm-white/dark-green appearance, T-shaped logo, and Taxora name, and requested email sign-in/registration. Scope includes registration, email verification, sign-in, password recovery/update, sign-out, and isolation of personal cloud cases.

The sign-in page uses two columns, showing only the form on mobile. The workspace retains the chat layout; the sidebar becomes light green with account/sign-out entry points. Retain language switching and reduced-motion preferences; animation must not add network waiting time.

Implementation order: authentication backend → bind account identity to existing cases → sign-in/recovery forms → workspace mounting/sign-out cleanup → isolation/browser regression → actual verification after email configuration.

Supabase handles authentication and passwords. The backend calls the fixed, configured Auth API; tokens use HttpOnly cookies. The remotely validated UUID of a confirmed-email user is the sole case identity. Missing configuration disables case access with no anonymous fallback. Old cookie cases do not migrate automatically; organization roles and professional approval are out of scope.

Classify errors as authentication failure, unverified email, rate limiting, or unavailable service without passing raw provider exceptions to the page. Email-sent pages do not disclose account existence. Recovery callbacks remove URL tokens, check that access and refresh tokens identify the same user, and establish cookies. Regression must cover rejected cross-account reads/writes, session recovery, registration validation, recovery pages, language, and mobile layouts.

UI and APIs may be completed first; actual email depends on the project URL, public API key, callbacks, and SMTP. Substitute tests are not cloud registration acceptance.
