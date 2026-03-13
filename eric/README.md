# Eric: AI Assistant for Email

See: https://youtu.be/35BIC1EBFx8

Eric is a Python-based assistant that works with your mailbox over IMAP and can use either:

- a local model via the Ollama API, or
- an OpenAI model via the OpenAI API.

At runtime, Eric:

1. Connects to your mailbox.
2. Reads the current inbox message list.
3. Waits for your instruction.
4. Builds a prompt from:
   - `SOUL.md`
   - the current inbox message list
   - your instruction

## Quick Start

## 1. Prerequisites

- Python 3.x
- IMAP enabled for your mailbox
- Mailbox credentials (app passwords strongly recommended)
- One model provider configured:
  - Ollama running locally, or
  - OpenAI API key (`OPENAI_API_KEY`)

## 2. Prepare Ollama

The default model is `gpt-oss:20b` (override with `--model`).

```bash
ollama pull gpt-oss:20b
```

For Ollama API details, see: https://docs.ollama.com/api/

## 3. Configure mailbox auth

By default, Eric loads `~/.eric/auth.ini` when `-m` and `-a` are not provided.

Create the file with one of the following formats.

Single mailbox format (backward compatible):

```ini
[imap]
mailbox = mailbox@example.com
password = app-password-here
server = imap.example.com
```

Multiple mailbox format:

```ini
[mailbox:personal]
mailbox = personal@example.com
password = personal-app-password
server = imap.example.com

[mailbox:work]
mailbox = work@example.com
password = work-app-password
server = outlook.office365.com
```

On Unix-like systems, lock down permissions:

```bash
chmod 600 ~/.eric/auth.ini
```

## 4. Run Eric

Run Eric using your project entry point (for example, `eric` if installed as a command) and pass options as needed:

```bash
eric --help
```

Typical examples:

```bash
# Single mailbox via flags
eric -m mailbox@example.com -s imap.example.com

# Use configured profiles from auth file
eric -a ~/.eric/auth.ini --profile personal

# Use OpenAI provider (API key from OPENAI_API_KEY)
eric --provider openai --model gpt-5.2

# Use OpenAI provider with explicit API key
eric --provider openai --model gpt-5.2 --openai-api-key sk-...
```

If `-m` is omitted, Eric runs all configured profiles from the auth file.  
Use `--profile <name>` (repeatable) to run only selected `[mailbox:<name>]` sections.

## CLI Options

- `-m`: mailbox email address (required unless provided via `-a`)
- `-a`, `--auth-file`: auth file path (optional)
- `--profile`: mailbox profile from auth file (repeatable); cannot be used with `-m`
- `-p`: mailbox password (optional; prompt shown if omitted)
- `-s`: IMAP server hostname (optional)
- `--model`: model name (default: `gpt-oss:20b`)
- `--provider`: model provider (`ollama` or `openai`, default `ollama`)
- `--openai-api-key`: OpenAI API key (optional if `OPENAI_API_KEY` is set)

## Privacy and Security Notes

- Eric uses IMAP credentials to access your mailbox; prefer app passwords over account passwords.
- Email content and metadata included in prompts are sent to your configured model provider.
- With Ollama, inference stays local on your machine.
- With OpenAI, prompt content is sent to OpenAI's API endpoint.
- Store auth files outside source control and keep file permissions restrictive.

## IMAP Provider Notes

- Gmail: enable IMAP and use an app password with 2FA-enabled accounts.
- Outlook / Microsoft 365: IMAP should be enabled in account settings; server is often `outlook.office365.com`.
- Other providers: confirm IMAP hostname, SSL/TLS requirements, and app-password support.

## Troubleshooting

- Authentication errors:
  - Verify mailbox, password/app password, and IMAP access settings.
  - Confirm auth file section names and keys are correct.
- Connection failures:
  - Re-check IMAP server hostname.
  - Confirm firewall/network access and provider IMAP port requirements.
- Ollama/model errors:
  - Ensure Ollama is running locally.
  - Pull the model before running (`ollama pull gpt-oss:20b`).
  - Override model via `--model` if needed.
- OpenAI/model errors:
  - Set `OPENAI_API_KEY` or pass `--openai-api-key`.
  - Use `--provider openai`.
  - Pass a valid OpenAI model name via `--model`.
