# Voice PubMed Reader: setup for Andrew

Prepared September 18, 2026. Steve has tested the hosted reader successfully;
Andrew's device setup and independent use still need the checks below.

## What to install

Use the hosted website on Andrew's iPhone, iPad and Mac:
https://vpr.157-151-155-75.sslip.io

There is nothing to download from the App Store. No Terminal, Python, ChatGPT
subscription or API key is needed on Andrew's devices. Internet access is required.
The iPhone/iPad works with his Mac switched off. CardioClaw is a separate service.

Ask Steve for the private VPR access code. Steve has it in Documents, in
“VPR private access.txt”. Send the code privately; it is not included in this
guide. This setup uses Steve's configured API billing.

## First setup on each device

1. Open the website in Safari, outside Private Browsing.
2. Enter the private access code and choose Sign in. Save it in Passwords if
   offered; otherwise add a Passwords entry for this website with the code as
   its password. The form has no username; use a descriptive label if Passwords
   requires one. Confirm that Andrew can retrieve or autofill it with VoiceOver.
3. Set Andrew's usual headphones or speaker and a comfortable volume.
4. Activate Start voice and allow microphone access when asked. With VoiceOver,
   focus Start voice and activate it using his normal VoiceOver gesture.
5. Wait for “PubMed ready. I am listening.” Then speak a search.
6. Choose End session when finished. “Stop” stops narration; it does not end
   the microphone session. Keep only one active reader session open.

Sign-in lasts up to eight hours and may expire sooner after a server update.
Check that Andrew can sign back in independently. Do not put the access code in
an address, shared shortcut, or this guide.

## Easy launch and Siri — all devices

In Apple's Shortcuts app, create a shortcut named “Read PubMed”. Add a URL action
containing https://vpr.157-151-155-75.sslip.io, followed by Open URLs. Run it once,
then test “Siri, Read PubMed”. Use the website URL, not an Open App action pointing
to Steve's locally installed launcher. If Siri does not recognize the phrase,
try “Siri, run Read PubMed”.

Siri opens the reader. Andrew must still sign in when necessary and activate
Start voice. It does not bypass device unlock or microphone permission.

On iPhone/iPad, also add an icon: in Safari choose Share → Add to Home Screen,
name it “Voice PubMed Reader”, then Add. If offered “Open as Web App”, leave it
off initially to use the Safari workflow. If you choose app mode, repeat the
sign-in, microphone and listening checks there; it may have separate permissions.

On Mac, bookmark the website in Safari Favorites. On macOS Sonoma or later,
File → Add to Dock can create a separate web app; repeat sign-in and microphone
checks if using it. The Siri shortcut is sufficient if Add to Dock is unavailable.

Apple references:
- https://support.apple.com/en-asia/guide/shortcuts/apd07c25bb38/ios
- https://support.apple.com/guide/iphone/open-as-web-app-iphea86e5236/ios
- https://support.apple.com/en-ie/104996

## Five-minute listening check with Andrew

Start with his Mac off when testing the iPhone/iPad. Have Andrew operate these
himself using his usual accessibility settings:

1. “Search PubMed for atrial fibrillation.” Listen for count, position and title.
2. “Read the abstract.” Interrupt with “Stop”. Confirm speech stops.
3. “Repeat.” Then “Next article” and “Previous article”.
4. “Who are the authors?” “What journal?” “What's the PMID?” “Read the citation.”
5. “Read the full text.” If unavailable, the reader should say so and wait.
   If available, try “What sections are available?” and “Go to results”.
6. “Keep reading” requests the next passage. Silence should not advance.
7. End session, reopen using Siri, and confirm he can start again independently.

Abstracts normally omit author/journal details. These are available on request.
Full text is limited to retrievable PMC text; a PubMed entry does not guarantee
full text. Reading uses passages; time skipping is approximate. Keep the reader
on screen while listening. Locked-screen/background playback is not verified.

## If something goes wrong

For sign-in problems, open https://vpr.157-151-155-75.sslip.io/login and retry
with the private access code. After an update, reload and sign in again.
For no sound, check volume and audio destination, End session, then Start voice.
For denied microphone permission, allow the website microphone in Safari settings
and retry. Do not change Andrew's normal accessibility configuration unnecessarily.

Tell Steve the device, command, exact error and article title or PMID. Do not send
access codes or API keys in troubleshooting screenshots. This guide contains no
credentials and can be shared with Andrew's son.
