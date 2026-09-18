# Independent VPR hosting — September 18, 2026

Prepared on the existing Oracle server (157.151.155.75) with its own Linux
account `vpr`, application `/opt/vpr`, environment folder `/etc/vpr`, data
`/var/lib/vpr`, and `vpr.service`. The process listens on loopback port 8080.
It has a separate Python environment, a 256 MB memory cap and 50% CPU quota.
No CardioClaw source, credentials, data, schedules or service settings were changed.
The existing Caddy HTTPS gateway can serve both applications with different names.

## Current status

**Activated September 18, 2026 after Steve explicitly approved transferring the
existing VPR API key.** The key is stored in the root-only cloud environment file.
VPR is enabled at boot. Public TLS, health, private sign-in, authenticated reader
and unauthenticated voice-request rejection all passed. CardioClaw services and
Caddy remained active. No microphone or paid voice session was started.

Live address: https://vpr.157-151-155-75.sslip.io
Private access instructions are in `~/Documents/VPR private access.txt` (mode 600),
outside Git. No credentials are committed. Mobile listening remains unverified.

The temporary address depends on third-party sslip.io DNS and the server IP.
A permanent user-owned domain can replace it later.

## Activation after credential permission

Provide a VPR OpenAI API key in `/etc/vpr/environment` (root-only mode 600),
plus VPR_ACCESS_CODE (at least 32 random characters), VPR_PUBLIC_ORIGIN,
NCBI_EMAIL, VPR_DATA_DIR=/var/lib/vpr and PORT=8080. Never commit this file.
Steve explicitly approved copying the existing VPR key before activation.
Do not reuse CardioClaw credentials.

Back up `/etc/caddy/Caddyfile`, append the prepared `/opt/vpr/vpr.caddy`
block without modifying the existing block, validate Caddy configuration,
then enable/start only vpr.service and reload Caddy. Verify TLS, health,
login, authenticated page and rejected unauthenticated tool requests.
Verify the other services remain active. Do not start microphone/audio.
For rollback stop/disable vpr.service and remove only its Caddy block.
Preserve all VPR data and the prior Caddy configuration.

## Private access and device testing

Access-code sign-in sets an eight-hour Secure, HttpOnly, SameSite cookie.
Each signed-in browser receives an independent reader and CSRF token.
Login and voice-session starts are rate limited. The service is intended for
private use by Steve/Andrew; it is not a public multi-user hosting platform.
Saved references share VPR's own data file. Reader state is in memory.
Restarting expires logins. There is no account-management or logout UI yet.

On iPhone/iPad, open the HTTPS link in Safari, save the access code in Passwords,
and sign in. Add a Home Screen shortcut or a Siri shortcut named Read PubMed
that opens that link. Activate Start voice yourself and allow microphone access.
Siri launches the page; it does not bypass sign-in or microphone permission.
Keep the page open while reading. Background/lock-screen behavior is unverified.
Test with Andrew's Mac off: search, title, abstract, interrupt, next/previous,
repeat, full text and sections. Only Andrew's successful independent audible
use establishes acceptance. Existing Realtime engine and PubMed backend remain
unchanged; Muse stays a local Mac fallback.
