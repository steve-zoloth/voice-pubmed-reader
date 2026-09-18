# Current baseline — audited September 11, 2026

The current working Voice PubMed Reader is **voice-pubmed-reader on realtime-reader**,
using **GPT-Realtime-2.1 over browser WebRTC**. It is not the old VoicePubMedWeb
Flask app, not Researcher Pro, and not GPT-Live. Read AGENTS.md first.

Canonical repository: https://github.com/steve-zoloth/voice-pubmed-reader
Canonical branch: https://github.com/steve-zoloth/voice-pubmed-reader/tree/realtime-reader
Local checkout: /Users/stevezoloth/Documents/voice_pubmed_bot

## Launch the established reader

From Finder, open run_realtime_pubmed.command in this repository. The command
loads the existing .env through the original launcher and opens the Realtime
browser UI. Activate Start voice yourself when ready. Do not use a relative path
copied from a chat link; that previously caused repeated launch errors.

Terminal equivalent:

```bash
bash "$HOME/Documents/voice_pubmed_bot/run_realtime_pubmed.command"
```

The AI voice is Marin. The retained Muse/Nova fallback uses
run_voice_pubmed_bot.command (same directory). End one voice session before
starting the other. No further API purchase or microphone reconfiguration is
part of the baseline restoration.

## Verified history and present code

| Area | Audited state |
| --- | --- |
| Real voice interaction | Steve: “wow that works really well, allows interrupts” on Sept 10; later explicitly preferred it to Muse. |
| Search and navigation | Existing Entrez backend, next/previous, more results, total vs loaded counts, article-position announcements. |
| Reading | Structured abstract without routine author/affiliation preamble; PMC full text when available; authors on request. |
| Sections | Actual source headings; methods/results/conclusions and list-sections commands. No invented sections. |
| Review articles | PubMed publication-type labels, review filtering, and article-type queries. |
| Concision | Explicit short-answer/no-routine-menu instructions; still subject to live model behavior. |
| Interruption | Browser AEC and duplex; suppress late narration; cancel superseded queued commands. In-flight retrieval may still update state. |
| Repeat | Preserves passage after informational questions such as counts/authors. |
| Skip/resume | Time skip estimates source words; resume/repeat restarts a passage. No exact audio seek or word-level resume. |
| Long reading | Explicit passages up to 180 words; continue requests another passage. Silence does not advance. |
| Fallback | Muse streaming recognition and Nova narration/playback remain in the repository. |
| Billing | User confirmed $10 API credit and auto-recharge on Sept 11. ChatGPT credits were a separate purchase. |

Core files: realtime_adapter.py, realtime_reader.html, structured_reader.py,
voice_pubmed_bot.py, nova_speech.py, muse_stt.py, playback_controls.py.

## Latest validation

September 11 audit: **41 offline tests passed** using the five test modules below.
No microphone, speech generation, or live audio was started for that verification.
Earlier task evidence also records browser interruption checks and controlled
launcher routing checks. Steve confirmed the Sept 10 Realtime experience worked;
the most recent Sept 11 refinements still need an audible user acceptance test
now that billing is fixed. Do not conflate that with reopening solved microphone
or speech-engine design work.

```bash
python3 -B -m unittest -q test_voice_output test_playback_controls test_more_results test_structured_reader test_realtime_adapter
```

## Still required

Andrew's independent launch/voice workflow test remains the acceptance gate.
Verify sound reaching him, accurate medical reading, interrupt/stop/repeat,
next/previous, full-text availability/failure, sections and recovery. Keep his
normal device setup; investigate only a reproduced failure in this version.

Broader named libraries, citation-network browsing, APA/BibTeX export, and DOI
publisher access belong to the older Researcher Pro repository. They are not
all implemented in this newer voice reader. Preserve their code as reference;
any consolidation is a separate scoped task, not silent deletion or rewriting.

## Git checkpoint

Before this audit, HEAD was a745c08 and the working Realtime files were untracked;
GitHub therefore did not contain the tested interface or its enhancements.
The checkpoint commit containing this file records those existing source files,
tests and audit instructions on realtime-reader. The external audit report records
the resulting commit and push verification; use Git history for the exact hash.
See PROJECT_HISTORY_AUDIT.md for the full evidence and version map.

## Repository rename — September 11, 2026

At Steve's request, GitHub repository voice_pubmed_bot was renamed to
voice-pubmed-reader, and branch muse-upgrade to realtime-reader. The latter is
now the GitHub default branch. Both names refer to the same preserved Git
history, not a rebuilt app. The local directory and launcher names stay as
documented above so existing launch paths continue to work.

Before renaming, local source and origin/muse-upgrade matched checkpoint
da6237f3523c4f96c2cdee925336281860f01652 exactly, and all 41 offline tests passed.
After renaming, the GitHub branch retained that exact commit. This update changes
repository names and documentation only; application/audio code is unchanged.
The Sept 10 user-approved Realtime experience and Sept 11 enhancements are
preserved. The later enhancements still require the user's audible retest.

## Startup accessibility — September 12, 2026

Steve reported that silent launch gave no indication the reader was present or
waiting for input. The launcher now speaks a short opening instruction using
the existing Nova output before opening the browser. Start voice has autofocus
so Enter activates it. After connection the existing Marin greeting explicitly
says “PubMed ready. I am listening.” Microphone activation remains user initiated.
Startup speech failure prints a recovery instruction; it does not prevent launch.
This change is included in the September 18 startup-accessibility checkpoint
on realtime-reader. Audible user verification remains outstanding.
All 41 offline tests passed again on September 18; no microphone or audio
was activated. The previous checkpoint is 4a28236; Git history records the
new checkpoint hash.

## User acceptance and next refinements — September 18, 2026

Steve tested checkpoint e21558c and reported the startup/basic flow and further
functions all worked. Remaining feedback: too chatty and long pauses after new
instructions. This supersedes the earlier pending Steve acceptance statements;
Andrew's independent-use acceptance remains outstanding.

New refinements prohibit spoken pre-tool acknowledgments and post-reading chatter,
use configurable high semantic-VAD eagerness (auto restores the old wait), and
cache up to 12 successfully retrieved sources per session. 44 offline tests pass.
These refinements require a listening check; improvement has not been measured.

mac_app contains a native Mac launcher and reproducible builder. Steve's app is
installed at ~/Applications/Voice PubMed Reader.app and uses the existing local
checkout/environment. Native compilation and signature checks pass. UI lifecycle
verification is blocked by computer-use permissions, not a confirmed app failure.
No live audio was started for verification. End session in the browser before
quitting the launcher. See ANDREW_SETUP.md for Siri setup and installation limits.
Andrew wants both Mac and iPhone/iPad. Mobile secure hosting/private-access choice
is pending; no mobile deployment or self-contained Andrew installer is claimed.

## Independent hosting preparation — September 18, 2026

Steve selected a separate service in his existing cloud account and confirmed
CardioClaw and VPR serve different purposes; he eventually wants to share both.
VPR has its own cloud Linux user, folders, environment, data and disabled service.
47 offline tests pass; Linux import and service-definition checks pass. The
existing CardioClaw and HTTPS services remain active. No public VPR route or
API credentials are installed yet. Credential transfer was blocked by automatic
approval review pending explicit user permission. See HOSTED_SETUP.md.

The Mac Shortcuts app now contains Read PubMed -> Open Voice PubMed Reader.
It was not run. The dummy native launcher lifecycle test remains unverified:
automatic approval review requires explicit confirmation to launch that locally
built test app. No live microphone or speech was activated.

## Cloud activation — September 18, 2026

After explicit user permission, the existing VPR API key was installed in its
root-only cloud configuration and vpr.service enabled. VPR is live at
https://vpr.157-151-155-75.sslip.io independently of the Mac. TLS, health, private
sign-in, authenticated page and unauthenticated session rejection passed.
CardioClaw services remained active and their application configuration unchanged.
Private access instructions are in ~/Documents/VPR private access.txt, outside Git.
No voice session was started; iPhone/iPad listening and Andrew acceptance remain
pending. Prior blocked credential-transfer status is superseded by this approval.

Login recovery: /login now always shows the sign-in form, including when already
signed in. Rejected login origins include a Return to login link. Same-origin
referrer policy preserves same-site form metadata. Four hosted tests pass; live
login page verified. User retry is still needed to confirm reported rejection.

Cloud retrieval fix: reproduced search failure under service restrictions because
Entrez tried to create its XML parser cache in read-only /opt/vpr/.config. Hosted
startup now sets Entrez.local_cache to /var/lib/vpr/entrez-cache. Deployed and
verified live search (five articles), pagination (ten), and abstract retrieval
under the same filesystem restrictions. 25 relevant offline tests passed.
No voice or microphone was started.

On-request citation metadata: added journal, pmid and citation tool actions;
existing authors action retained. Citation returns title, authors, journal and
PMID using PubMed independently of PMC availability. Metadata requests preserve
the prior reading passage; abstract defaults remain unchanged. 50 offline tests
passed and live hosted journal/PMID/citation checks passed. Deployed to VPR only.
Steve reports hosted reader seems to work; mobile audible metadata retry remains.
