#!/usr/bin/env python3
"""Eric: connect to IMAP inbox, then send user prompts to a model provider."""

from __future__ import annotations

import argparse
import configparser
import email
import getpass
import imaplib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from email.header import decode_header
from email.utils import make_msgid, parseaddr
from typing import Iterable


DEFAULT_AUTH_FILE = os.path.expanduser("~/.eric/auth.ini")
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
SOUL_FILE = "SOUL.md"
TOOL_SPEC = """Available tool action (JSON only):
{"action":"list_messages","args":{"mailbox":"<mailbox_profile_name_optional>","limit":20}}
{"action":"search_messages","args":{"query":"<text_query_optional>","mailbox":"<mailbox_profile_name_optional>","limit":20}}
{"action":"read_message","args":{"message_id":"123","mailbox":"<mailbox_profile_name_optional>"}}
{"action":"read_thread","args":{"message_id":"123","mailbox":"<mailbox_profile_name_optional>"}}
{"action":"create_draft","args":{"to":"recipient@example.com","subject":"Subject text","body":"Draft body text","mailbox":"<mailbox_profile_name_optional>","in_reply_to":"<message_id_optional>","cc":"<comma_separated_addresses_optional>","bcc":"<comma_separated_addresses_optional>"}}
{"action":"create_reply_draft","args":{"message_id":"123","body":"Draft reply text","mailbox":"<mailbox_profile_name_optional>","cc":"<comma_separated_addresses_optional>","bcc":"<comma_separated_addresses_optional>"}}
{"action":"mark_read","args":{"message_id":"123","mailbox":"<mailbox_profile_name_optional>"}}
{"action":"mark_unread","args":{"message_id":"123","mailbox":"<mailbox_profile_name_optional>"}}
{"action":"archive_message","args":{"message_id":"123","mailbox":"<mailbox_profile_name_optional>"}}
Rules:
- If you want to call a tool, respond with ONLY a JSON object.
- Use only the actions "list_messages", "search_messages", "read_message", "read_thread", "create_draft", "create_reply_draft", "mark_read", "mark_unread", and "archive_message".
- If the user asks about a specific message's contents, call read_message first.
- Never send placeholder values literally (for example "<mailbox_profile_name_optional>"); use a real value or omit optional fields.
- If no tool is needed, respond normally in plain text."""


@dataclass
class MailboxConfig:
    name: str
    mailbox: str
    password: str | None
    server: str | None


@dataclass
class InboxMessage:
    mailbox_name: str
    mailbox_address: str
    message_id: str
    subject: str
    sender: str
    date: str


def derive_imap_server(mailbox: str) -> str:
    if "@" not in mailbox:
        raise ValueError(f"Invalid mailbox address: {mailbox}")

    domain = mailbox.rsplit("@", 1)[1].lower().strip()
    provider_map = {
        "gmail.com": "imap.gmail.com",
        "googlemail.com": "imap.gmail.com",
        "outlook.com": "outlook.office365.com",
        "hotmail.com": "outlook.office365.com",
        "live.com": "outlook.office365.com",
        "msn.com": "outlook.office365.com",
        "yahoo.com": "imap.mail.yahoo.com",
        "icloud.com": "imap.mail.me.com",
        "me.com": "imap.mail.me.com",
        "mac.com": "imap.mail.me.com",
    }
    return provider_map.get(domain, f"imap.{domain}")


def decode_mime_header(value: str | None) -> str:
    if not value:
        return ""
    decoded_parts: list[str] = []
    for part, charset in decode_header(value):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
            except LookupError:
                decoded_parts.append(part.decode("utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Connect to IMAP inbox, list messages, then send a prompt to the selected model provider."
    )
    parser.add_argument(
        "-m",
        dest="mailbox",
        help="Mailbox email address (required unless provided via auth file).",
    )
    parser.add_argument(
        "-a",
        "--auth-file",
        dest="auth_file",
        help="Path to auth INI file.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Mailbox profile name from auth file. Repeatable.",
    )
    parser.add_argument(
        "-p",
        dest="password",
        help="Mailbox password. If omitted for CLI mailbox, prompt is shown.",
    )
    parser.add_argument(
        "-s",
        dest="server",
        help="IMAP server hostname.",
    )
    parser.add_argument(
        "--model",
        default="gpt-oss:20b",
        help="Model name (default: gpt-oss:20b).",
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "openai"],
        default="ollama",
        help="Model provider (default: ollama).",
    )
    parser.add_argument(
        "--openai-api-key",
        help="OpenAI API key. If omitted, OPENAI_API_KEY is used.",
    )
    parser.add_argument(
        "--debug-prompt",
        action="store_true",
        help="Print the composed prompt before sending it to the model API.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-approve all tool operations without interactive confirmation.",
    )
    parser.add_argument(
        "--noguardrail",
        action="store_true",
        help="Disable the per-user-turn tool-round guardrail.",
    )
    return parser.parse_args()


def load_auth_file(path: str) -> configparser.ConfigParser:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Auth file not found: {path}")

    parser = configparser.ConfigParser()
    read_files = parser.read(path)
    if not read_files:
        raise ValueError(f"Unable to read auth file: {path}")
    return parser


def load_profiles_from_auth(
    cfg: configparser.ConfigParser,
    selected_profiles: Iterable[str],
) -> list[MailboxConfig]:
    selected = set(selected_profiles)
    mailboxes: list[MailboxConfig] = []

    profile_sections = [s for s in cfg.sections() if s.startswith("mailbox:")]

    if profile_sections:
        available = {s.split("mailbox:", 1)[1]: s for s in profile_sections}
        targets = selected or set(available.keys())
        missing = sorted(name for name in targets if name not in available)
        if missing:
            raise ValueError(
                "Requested profile(s) not found in auth file: " + ", ".join(missing)
            )

        for profile in sorted(targets):
            section = cfg[available[profile]]
            mailboxes.append(
                MailboxConfig(
                    name=profile,
                    mailbox=section.get("mailbox", "").strip(),
                    password=section.get("password"),
                    server=section.get("server"),
                )
            )
    elif cfg.has_section("imap"):
        if selected:
            raise ValueError(
                "--profile was provided, but auth file has no [mailbox:<name>] sections."
            )
        section = cfg["imap"]
        mailboxes.append(
            MailboxConfig(
                name="imap",
                mailbox=section.get("mailbox", "").strip(),
                password=section.get("password"),
                server=section.get("server"),
            )
        )
    else:
        raise ValueError(
            "Auth file must contain [imap] or [mailbox:<name>] section(s)."
        )

    for cfg_item in mailboxes:
        if not cfg_item.mailbox:
            raise ValueError(f"Missing 'mailbox' value for profile '{cfg_item.name}'.")
        if not cfg_item.server:
            cfg_item.server = derive_imap_server(cfg_item.mailbox)

    return mailboxes


def resolve_mailboxes(args: argparse.Namespace) -> list[MailboxConfig]:
    if args.mailbox and args.profile:
        raise ValueError("--profile cannot be used with -m.")

    if args.mailbox:
        password = args.password or getpass.getpass(f"Password for {args.mailbox}: ")
        server = args.server or derive_imap_server(args.mailbox)
        return [
            MailboxConfig(
                name=args.mailbox,
                mailbox=args.mailbox,
                password=password,
                server=server,
            )
        ]

    auth_file = args.auth_file or DEFAULT_AUTH_FILE
    cfg = load_auth_file(auth_file)
    mailboxes = load_profiles_from_auth(cfg, args.profile)

    for mb in mailboxes:
        if not mb.password:
            mb.password = getpass.getpass(f"Password for {mb.mailbox}: ")

    return mailboxes


def load_soul(path: str = SOUL_FILE) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"SOUL file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def list_inbox_messages(config: MailboxConfig) -> list[InboxMessage]:
    print(f"\n== {config.name} ({config.mailbox}) ==")
    print(f"Connecting to {config.server} ...")
    try:
        with imaplib.IMAP4_SSL(config.server) as imap:
            imap.login(config.mailbox, config.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            status, data = imap.search(None, "ALL")
            if status != "OK":
                raise RuntimeError("Could not search INBOX.")

            ids = (data[0] or b"").split()
            messages: list[InboxMessage] = []
            print(f"Found {len(ids)} message(s) in INBOX.")
            if not ids:
                imap.logout()
                return messages

            for msg_id in ids:
                status, msg_data = imap.fetch(
                    msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
                )
                if status != "OK" or not msg_data or not msg_data[0]:
                    print(f"{msg_id.decode(errors='replace')}: <unable to fetch header>")
                    continue

                raw_header = msg_data[0][1]
                if not isinstance(raw_header, (bytes, bytearray)):
                    print(f"{msg_id.decode(errors='replace')}: <unexpected header format>")
                    continue

                parsed = email.message_from_bytes(raw_header)
                subject = decode_mime_header(parsed.get("Subject"))
                sender = decode_mime_header(parsed.get("From"))
                date = decode_mime_header(parsed.get("Date"))
                msg_num = msg_id.decode(errors="replace")
                message = InboxMessage(
                    mailbox_name=config.name,
                    mailbox_address=config.mailbox,
                    message_id=msg_num,
                    subject=subject or "(no subject)",
                    sender=sender or "(unknown sender)",
                    date=date or "(unknown date)",
                )
                messages.append(message)
                print(f"{message.message_id}. {message.subject}")
                print(f"   From: {message.sender}")
                print(f"   Date: {message.date}")

            imap.logout()
            return messages
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP error for {config.mailbox}: {exc}") from exc


def parse_chat_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def chat_with_ollama(model: str, messages: list[dict[str, str]]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not reach Ollama API at http://localhost:11434. Is Ollama running?"
        ) from exc

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid JSON response from Ollama API.") from exc

    content = parse_chat_content(parsed.get("message", {}).get("content"))
    if not content:
        raise RuntimeError("Ollama response did not include message.content.")
    return content


def chat_with_openai(
    model: str,
    messages: list[dict[str, str]],
    api_key: str,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not reach OpenAI API at https://api.openai.com.") from exc

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid JSON response from OpenAI API.") from exc

    choices = parsed.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenAI response did not include choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("OpenAI response choices[0] was invalid.")
    message = first.get("message", {})
    if not isinstance(message, dict):
        raise RuntimeError("OpenAI response did not include message object.")
    content = parse_chat_content(message.get("content"))
    if not content:
        raise RuntimeError("OpenAI response did not include message.content.")
    return content


def chat_with_model(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    openai_api_key: str | None,
) -> str:
    if provider == "ollama":
        return chat_with_ollama(model, messages)
    if provider == "openai":
        key = (openai_api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        if not key:
            raise RuntimeError(
                "OpenAI API key is required. Set OPENAI_API_KEY or pass --openai-api-key."
            )
        if model == "gpt-oss:20b":
            raise RuntimeError(
                "When using --provider openai, pass an OpenAI model with --model."
            )
        return chat_with_openai(model, messages, key)
    raise RuntimeError(f"Unsupported model provider: {provider}")


def parse_tool_requests(reply: str) -> list[dict[str, object]]:
    text = reply.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    parsed_requests: list[dict[str, object]] = []
    decoder = json.JSONDecoder()
    idx = 0
    length = len(text)
    while idx < length:
        while idx < length and text[idx].isspace():
            idx += 1
        if idx >= length:
            break
        try:
            data, next_idx = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break
        if isinstance(data, dict) and isinstance(data.get("action"), str):
            parsed_requests.append(data)
        idx = next_idx
    return parsed_requests


def get_model_reply(
    provider: str,
    model: str,
    history: list[dict[str, str]],
    openai_api_key: str | None,
    max_attempts: int = 3,
) -> str:
    for attempt in range(1, max_attempts + 1):
        reply = chat_with_model(provider, model, history, openai_api_key)
        if reply.strip():
            return reply

        print(f"Model returned an empty response (attempt {attempt}/{max_attempts}).")
        history.append({"role": "assistant", "content": reply})
        history.append(
            {
                "role": "user",
                "content": (
                    "Your previous response was empty. "
                    "Respond now with either plain text or a JSON tool call."
                ),
            }
        )

    raise RuntimeError("Model returned empty responses repeatedly.")


def parse_address_field(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(parts)
    return ""


def parse_mailbox_name_from_list_line(line: str) -> str:
    match = re.search(r' "((?:[^"\\]|\\.)*)"\s*$', line)
    if match:
        return match.group(1).replace('\\"', '"')
    parts = line.rsplit(" ", 1)
    return parts[-1].strip('"') if parts else ""


def find_drafts_mailbox(imap: imaplib.IMAP4_SSL) -> str:
    status, boxes = imap.list()
    if status != "OK" or not boxes:
        return "Drafts"

    candidates: list[str] = []
    for raw in boxes:
        if not isinstance(raw, (bytes, bytearray)):
            continue
        line = raw.decode("utf-8", errors="replace")
        name = parse_mailbox_name_from_list_line(line)
        if name:
            candidates.append(name)

    preferred = [
        "[Gmail]/Drafts",
        "Drafts",
        "INBOX.Drafts",
    ]
    lower_map = {name.lower(): name for name in candidates}
    for option in preferred:
        if option.lower() in lower_map:
            return lower_map[option.lower()]

    for name in candidates:
        if "draft" in name.lower():
            return name

    return "Drafts"


def find_archive_mailbox(imap: imaplib.IMAP4_SSL) -> str:
    status, boxes = imap.list()
    if status != "OK" or not boxes:
        return "Archive"

    candidates: list[str] = []
    for raw in boxes:
        if not isinstance(raw, (bytes, bytearray)):
            continue
        line = raw.decode("utf-8", errors="replace")
        name = parse_mailbox_name_from_list_line(line)
        if name:
            candidates.append(name)

    preferred = [
        "[Gmail]/All Mail",
        "Archive",
        "INBOX.Archive",
    ]
    lower_map = {name.lower(): name for name in candidates}
    for option in preferred:
        if option.lower() in lower_map:
            return lower_map[option.lower()]

    for name in candidates:
        lname = name.lower()
        if "archive" in lname or "all mail" in lname:
            return name

    return "Archive"


def resolve_target_mailbox(
    mailboxes_by_name: dict[str, MailboxConfig],
    requested_name: str | None,
) -> MailboxConfig:
    if requested_name:
        target = mailboxes_by_name.get(requested_name)
        if not target:
            names = ", ".join(sorted(mailboxes_by_name.keys()))
            raise ValueError(
                f"Unknown mailbox '{requested_name}'. Available mailboxes: {names}"
            )
        return target

    if len(mailboxes_by_name) == 1:
        return next(iter(mailboxes_by_name.values()))

    names = ", ".join(sorted(mailboxes_by_name.keys()))
    raise ValueError(
        f"Multiple mailboxes configured. Specify 'mailbox' in the tool request. Available: {names}"
    )


def create_draft(
    mailbox: MailboxConfig,
    to_addr: str,
    subject: str,
    body: str,
    cc_addr: str = "",
    bcc_addr: str = "",
    in_reply_to: str = "",
) -> str:
    message = EmailMessage()
    message["From"] = mailbox.mailbox
    message["To"] = to_addr
    if cc_addr:
        message["Cc"] = cc_addr
    if bcc_addr:
        message["Bcc"] = bcc_addr
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to
    message.set_content(body)

    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            drafts_box = find_drafts_mailbox(imap)
            status, data = imap.append(
                drafts_box,
                r"(\Draft)",
                None,
                message.as_bytes(),
            )
            if status != "OK":
                raise RuntimeError(f"IMAP APPEND failed: {data}")
            imap.logout()
            return f"Draft created in '{drafts_box}' for mailbox '{mailbox.name}'."
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP draft creation failed for {mailbox.mailbox}: {exc}") from exc


def get_message_text_part(parsed: email.message.Message) -> str:
    if parsed.is_multipart():
        for part in parsed.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() != "text/plain":
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                return payload.decode(charset, errors="replace").strip()
            except LookupError:
                return payload.decode("utf-8", errors="replace").strip()

        for part in parsed.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() != "text/html":
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                html = payload.decode(charset, errors="replace")
            except LookupError:
                html = payload.decode("utf-8", errors="replace")
            return re.sub(r"<[^>]+>", " ", html).strip()
        return ""

    payload = parsed.get_payload(decode=True)
    if payload is None:
        return ""
    charset = parsed.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace").strip()
    except LookupError:
        return payload.decode("utf-8", errors="replace").strip()


def quote_text_for_reply(text: str) -> str:
    lines = text.splitlines() or [""]
    return "\n".join(f"> {line}" if line else ">" for line in lines)


def fetch_message_by_sequence_id(
    imap: imaplib.IMAP4_SSL,
    message_id: str,
) -> email.message.Message:
    status, data = imap.fetch(message_id, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        raise RuntimeError(f"Could not fetch message {message_id}.")

    raw = data[0][1]
    if not isinstance(raw, (bytes, bytearray)):
        raise RuntimeError(f"Unexpected message format for {message_id}.")
    return email.message_from_bytes(raw)


def format_parsed_message(parsed: email.message.Message, message_id: str, mailbox: MailboxConfig) -> str:
    subject = decode_mime_header(parsed.get("Subject")) or "(no subject)"
    sender = decode_mime_header(parsed.get("From")) or "(unknown sender)"
    date = decode_mime_header(parsed.get("Date")) or "(unknown date)"
    body = get_message_text_part(parsed)
    if not body:
        body = "(no text body found)"
    if len(body) > 20000:
        body = body[:20000] + "\n...[truncated]"
    return (
        f"Message {message_id}\n"
        f"Mailbox: {mailbox.name} ({mailbox.mailbox})\n"
        f"From: {sender}\n"
        f"Date: {date}\n"
        f"Subject: {subject}\n\n"
        f"Body:\n{body}"
    )


def read_message(mailbox: MailboxConfig, message_id: str) -> str:
    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")
            parsed = fetch_message_by_sequence_id(imap, message_id)
            imap.logout()
            return format_parsed_message(parsed, message_id, mailbox)
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP read failed for {mailbox.mailbox}: {exc}") from exc


def list_messages_tool(mailbox: MailboxConfig, limit: int = 20) -> str:
    if limit < 1:
        raise ValueError("list_messages 'limit' must be >= 1.")
    if limit > 200:
        raise ValueError("list_messages 'limit' must be <= 200.")

    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            status, data = imap.search(None, "ALL")
            if status != "OK":
                raise RuntimeError("Could not search INBOX.")

            ids = (data[0] or b"").split()
            if not ids:
                imap.logout()
                return f"Mailbox {mailbox.name} ({mailbox.mailbox}) has no messages in INBOX."

            selected_ids = list(reversed(ids[-limit:]))
            lines = [
                f"Mailbox: {mailbox.name} ({mailbox.mailbox})",
                f"Showing {len(selected_ids)} of {len(ids)} message(s), newest first:",
            ]

            for msg_id in selected_ids:
                status, msg_data = imap.fetch(
                    msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
                )
                if status != "OK" or not msg_data or not msg_data[0]:
                    lines.append(f"- {msg_id.decode(errors='replace')}: <unable to fetch header>")
                    continue

                raw_header = msg_data[0][1]
                if not isinstance(raw_header, (bytes, bytearray)):
                    lines.append(
                        f"- {msg_id.decode(errors='replace')}: <unexpected header format>"
                    )
                    continue

                parsed = email.message_from_bytes(raw_header)
                subject = decode_mime_header(parsed.get("Subject")) or "(no subject)"
                sender = decode_mime_header(parsed.get("From")) or "(unknown sender)"
                date = decode_mime_header(parsed.get("Date")) or "(unknown date)"
                msg_num = msg_id.decode(errors="replace")
                lines.append(
                    f"- ID: {msg_num} | From: {sender} | Date: {date} | Subject: {subject}"
                )

            imap.logout()
            return "\n".join(lines)
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP list failed for {mailbox.mailbox}: {exc}") from exc


def search_messages_tool(mailbox: MailboxConfig, query: str = "", limit: int = 20) -> str:
    if limit < 1:
        raise ValueError("search_messages 'limit' must be >= 1.")
    if limit > 200:
        raise ValueError("search_messages 'limit' must be <= 200.")

    needle = query.strip().lower()
    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            status, data = imap.search(None, "ALL")
            if status != "OK":
                raise RuntimeError("Could not search INBOX.")

            ids = (data[0] or b"").split()
            if not ids:
                imap.logout()
                return f"Mailbox {mailbox.name} ({mailbox.mailbox}) has no messages in INBOX."

            matches: list[str] = []
            for msg_id in reversed(ids):
                status, msg_data = imap.fetch(
                    msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
                )
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw_header = msg_data[0][1]
                if not isinstance(raw_header, (bytes, bytearray)):
                    continue

                parsed = email.message_from_bytes(raw_header)
                subject = decode_mime_header(parsed.get("Subject")) or "(no subject)"
                sender = decode_mime_header(parsed.get("From")) or "(unknown sender)"
                date = decode_mime_header(parsed.get("Date")) or "(unknown date)"
                summary = (
                    f"ID: {msg_id.decode(errors='replace')} | "
                    f"From: {sender} | Date: {date} | Subject: {subject}"
                )
                searchable = f"{sender} {subject} {date}".lower()
                if not needle or needle in searchable:
                    matches.append(f"- {summary}")
                if len(matches) >= limit:
                    break

            imap.logout()
            if not matches:
                if needle:
                    return (
                        f"No messages matched query '{query}' in mailbox "
                        f"{mailbox.name} ({mailbox.mailbox})."
                    )
                return (
                    f"No messages returned in mailbox {mailbox.name} ({mailbox.mailbox})."
                )

            header = (
                f"Mailbox: {mailbox.name} ({mailbox.mailbox})\n"
                f"Search query: {query or '(none)'}\n"
                f"Returned {len(matches)} message(s), newest first:"
            )
            return header + "\n" + "\n".join(matches)
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP search failed for {mailbox.mailbox}: {exc}") from exc


def read_thread_tool(mailbox: MailboxConfig, message_id: str) -> str:
    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            parsed = fetch_message_by_sequence_id(imap, message_id)
            target_msgid = decode_mime_header(parsed.get("Message-ID")).strip()
            refs = decode_mime_header(parsed.get("References")).strip()
            in_reply_to = decode_mime_header(parsed.get("In-Reply-To")).strip()

            chain_ids: list[str] = []
            for token in (refs + " " + in_reply_to + " " + target_msgid).split():
                if token.startswith("<") and token.endswith(">") and token not in chain_ids:
                    chain_ids.append(token)

            if not chain_ids:
                imap.logout()
                return "Thread headers not found; falling back to single message.\n\n" + format_parsed_message(parsed, message_id, mailbox)

            lines = [f"Thread for message {message_id} in {mailbox.name} ({mailbox.mailbox}):"]
            for msgid in chain_ids:
                status, search_data = imap.search(None, "HEADER", "Message-ID", f'"{msgid}"')
                if status != "OK" or not search_data or not search_data[0]:
                    lines.append(f"- Message-ID {msgid}: not found in INBOX")
                    continue
                seq_ids = search_data[0].split()
                seq_id = seq_ids[-1].decode(errors="replace")
                thread_msg = fetch_message_by_sequence_id(imap, seq_id)
                subject = decode_mime_header(thread_msg.get("Subject")) or "(no subject)"
                sender = decode_mime_header(thread_msg.get("From")) or "(unknown sender)"
                date = decode_mime_header(thread_msg.get("Date")) or "(unknown date)"
                body = get_message_text_part(thread_msg)
                if len(body) > 4000:
                    body = body[:4000] + "\n...[truncated]"
                lines.append(
                    f"- ID: {seq_id} | Message-ID: {msgid} | From: {sender} | Date: {date} | Subject: {subject}\n"
                    f"  Body:\n{body or '(no text body found)'}"
                )

            imap.logout()
            return "\n\n".join(lines)
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP thread read failed for {mailbox.mailbox}: {exc}") from exc


def create_reply_draft_tool(
    mailbox: MailboxConfig,
    message_id: str,
    body: str,
    cc_addr: str = "",
    bcc_addr: str = "",
) -> str:
    if not body.strip():
        raise ValueError("create_reply_draft requires non-empty 'body'.")
    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            original = fetch_message_by_sequence_id(imap, message_id)
            reply_to = decode_mime_header(original.get("Reply-To")).strip()
            from_hdr = decode_mime_header(original.get("From")).strip()
            target_to = reply_to or from_hdr
            addr_email = parseaddr(target_to)[1]
            if not addr_email:
                raise RuntimeError(f"Could not determine reply recipient for message {message_id}.")

            original_subject = decode_mime_header(original.get("Subject")) or "(no subject)"
            if original_subject.lower().startswith("re:"):
                reply_subject = original_subject
            else:
                reply_subject = f"Re: {original_subject}"

            original_msgid = decode_mime_header(original.get("Message-ID")).strip()
            original_date = decode_mime_header(original.get("Date")) or "(unknown date)"
            original_body = get_message_text_part(original) or "(no text body found)"
            if len(original_body) > 3000:
                original_body = original_body[:3000] + "\n...[truncated]"

            reply = EmailMessage()
            reply["From"] = mailbox.mailbox
            reply["To"] = target_to
            if cc_addr:
                reply["Cc"] = cc_addr
            if bcc_addr:
                reply["Bcc"] = bcc_addr
            reply["Subject"] = reply_subject
            if original_msgid:
                reply["In-Reply-To"] = original_msgid
                reply["References"] = original_msgid
            reply["Message-ID"] = make_msgid()
            combined_body = (
                f"{body.strip()}\n\n"
                f"On {original_date}, {from_hdr} wrote:\n"
                f"{quote_text_for_reply(original_body)}"
            )
            reply.set_content(combined_body)

            drafts_box = find_drafts_mailbox(imap)
            status, data = imap.append(drafts_box, r"(\Draft)", None, reply.as_bytes())
            if status != "OK":
                raise RuntimeError(f"IMAP APPEND failed: {data}")
            imap.logout()
            return (
                f"Reply draft created in '{drafts_box}' for mailbox '{mailbox.name}'. "
                f"Target message ID: {message_id}."
            )
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP reply draft creation failed for {mailbox.mailbox}: {exc}") from exc


def mark_message_seen(mailbox: MailboxConfig, message_id: str, seen: bool) -> str:
    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            if seen:
                status, data = imap.store(message_id, "+FLAGS.SILENT", r"(\Seen)")
            else:
                status, data = imap.store(message_id, "-FLAGS.SILENT", r"(\Seen)")
            if status != "OK":
                raise RuntimeError(f"Could not update flags for message {message_id}: {data}")

            imap.logout()
            state = "read" if seen else "unread"
            return f"Message {message_id} marked as {state} in mailbox '{mailbox.name}'."
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP flag update failed for {mailbox.mailbox}: {exc}") from exc


def archive_message_tool(mailbox: MailboxConfig, message_id: str) -> str:
    try:
        with imaplib.IMAP4_SSL(mailbox.server or "") as imap:
            imap.login(mailbox.mailbox, mailbox.password or "")
            status, _ = imap.select("INBOX")
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")

            archive_box = find_archive_mailbox(imap)
            status, copy_data = imap.copy(message_id, archive_box)
            if status != "OK":
                raise RuntimeError(f"Could not copy message {message_id} to '{archive_box}': {copy_data}")

            status, store_data = imap.store(message_id, "+FLAGS.SILENT", r"(\Deleted)")
            if status != "OK":
                raise RuntimeError(f"Could not mark message {message_id} as deleted: {store_data}")

            status, expunge_data = imap.expunge()
            if status != "OK":
                raise RuntimeError(f"Could not expunge deleted message {message_id}: {expunge_data}")

            imap.logout()
            return (
                f"Message {message_id} archived to '{archive_box}' "
                f"in mailbox '{mailbox.name}'."
            )
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"IMAP archive failed for {mailbox.mailbox}: {exc}") from exc


def execute_tool_request(
    request: dict[str, object],
    mailboxes_by_name: dict[str, MailboxConfig],
    auto_yes: bool = False,
) -> str:
    action = request.get("action")
    raw_args = request.get("args")
    if not isinstance(raw_args, dict):
        raise ValueError("Tool call must include an object at 'args'.")

    if action == "list_messages":
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        raw_limit = raw_args.get("limit", 20)
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:
            raise ValueError("list_messages 'limit' must be an integer.") from exc
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print(
            f"\nModel requested action: list_messages (mailbox={target_mailbox.name}, limit={limit})"
        )
        return list_messages_tool(target_mailbox, limit=limit)

    if action == "search_messages":
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        query = str(raw_args.get("query", "")).strip()
        raw_limit = raw_args.get("limit", 20)
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:
            raise ValueError("search_messages 'limit' must be an integer.") from exc
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print(
            f"\nModel requested action: search_messages (mailbox={target_mailbox.name}, limit={limit}, query={query!r})"
        )
        return search_messages_tool(target_mailbox, query=query, limit=limit)

    if action == "read_message":
        message_id = str(raw_args.get("message_id", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        if not message_id:
            raise ValueError("read_message requires 'message_id'.")
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print(
            f"\nModel requested action: read_message (mailbox={target_mailbox.name}, id={message_id})"
        )
        return read_message(target_mailbox, message_id)

    if action == "read_thread":
        message_id = str(raw_args.get("message_id", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        if not message_id:
            raise ValueError("read_thread requires 'message_id'.")
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print(
            f"\nModel requested action: read_thread (mailbox={target_mailbox.name}, id={message_id})"
        )
        return read_thread_tool(target_mailbox, message_id)

    if action == "create_draft":
        to_addr = parse_address_field(raw_args.get("to"))
        subject = str(raw_args.get("subject", "")).strip()
        body = str(raw_args.get("body", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        in_reply_to = str(raw_args.get("in_reply_to", "")).strip()
        cc_addr = parse_address_field(raw_args.get("cc"))
        bcc_addr = parse_address_field(raw_args.get("bcc"))

        if not to_addr:
            raise ValueError("create_draft requires 'to'.")
        if not subject:
            raise ValueError("create_draft requires 'subject'.")
        if not body:
            raise ValueError("create_draft requires 'body'.")

        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)

        print("\nModel requested action: create_draft")
        print(f"Mailbox: {target_mailbox.name} ({target_mailbox.mailbox})")
        print(f"To: {to_addr}")
        if cc_addr:
            print(f"Cc: {cc_addr}")
        if bcc_addr:
            print(f"Bcc: {bcc_addr}")
        print(f"Subject: {subject}")
        print("Body:")
        print(body)

        approved = auto_yes or (
            input("Create this draft? [y/N]: ").strip().lower() in {"y", "yes"}
        )
        if not approved:
            return "Tool execution cancelled by user."

        return create_draft(
            mailbox=target_mailbox,
            to_addr=to_addr,
            subject=subject,
            body=body,
            cc_addr=cc_addr,
            bcc_addr=bcc_addr,
            in_reply_to=in_reply_to,
        )

    if action == "create_reply_draft":
        message_id = str(raw_args.get("message_id", "")).strip()
        body = str(raw_args.get("body", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        cc_addr = parse_address_field(raw_args.get("cc"))
        bcc_addr = parse_address_field(raw_args.get("bcc"))
        if not message_id:
            raise ValueError("create_reply_draft requires 'message_id'.")
        if not body:
            raise ValueError("create_reply_draft requires 'body'.")

        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print("\nModel requested action: create_reply_draft")
        print(f"Mailbox: {target_mailbox.name} ({target_mailbox.mailbox})")
        print(f"Target message ID: {message_id}")
        if cc_addr:
            print(f"Cc: {cc_addr}")
        if bcc_addr:
            print(f"Bcc: {bcc_addr}")
        print("Body:")
        print(body)

        approved = auto_yes or (
            input("Create this reply draft? [y/N]: ").strip().lower() in {"y", "yes"}
        )
        if not approved:
            return "Tool execution cancelled by user."

        return create_reply_draft_tool(
            mailbox=target_mailbox,
            message_id=message_id,
            body=body,
            cc_addr=cc_addr,
            bcc_addr=bcc_addr,
        )

    if action == "mark_read":
        message_id = str(raw_args.get("message_id", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        if not message_id:
            raise ValueError("mark_read requires 'message_id'.")
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print("\nModel requested action: mark_read")
        print(f"Mailbox: {target_mailbox.name} ({target_mailbox.mailbox})")
        print(f"Target message ID: {message_id}")
        approved = auto_yes or (
            input("Mark this message as read? [y/N]: ").strip().lower() in {"y", "yes"}
        )
        if not approved:
            return "Tool execution cancelled by user."
        return mark_message_seen(target_mailbox, message_id, seen=True)

    if action == "mark_unread":
        message_id = str(raw_args.get("message_id", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        if not message_id:
            raise ValueError("mark_unread requires 'message_id'.")
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print("\nModel requested action: mark_unread")
        print(f"Mailbox: {target_mailbox.name} ({target_mailbox.mailbox})")
        print(f"Target message ID: {message_id}")
        approved = auto_yes or (
            input("Mark this message as unread? [y/N]: ").strip().lower() in {"y", "yes"}
        )
        if not approved:
            return "Tool execution cancelled by user."
        return mark_message_seen(target_mailbox, message_id, seen=False)

    if action == "archive_message":
        message_id = str(raw_args.get("message_id", "")).strip()
        mailbox_name = str(raw_args.get("mailbox", "")).strip() or None
        if not message_id:
            raise ValueError("archive_message requires 'message_id'.")
        target_mailbox = resolve_target_mailbox(mailboxes_by_name, mailbox_name)
        print("\nModel requested action: archive_message")
        print(f"Mailbox: {target_mailbox.name} ({target_mailbox.mailbox})")
        print(f"Target message ID: {message_id}")
        approved = auto_yes or (
            input("Archive this message? [y/N]: ").strip().lower() in {"y", "yes"}
        )
        if not approved:
            return "Tool execution cancelled by user."
        return archive_message_tool(target_mailbox, message_id)

    raise ValueError(
        "Unsupported action. Allowed: 'list_messages', 'search_messages', 'read_message', 'read_thread', 'create_draft', 'create_reply_draft', 'mark_read', 'mark_unread', 'archive_message'."
    )


def format_messages_for_prompt(messages: list[InboxMessage]) -> str:
    if not messages:
        return "No messages found in inbox."

    lines: list[str] = []
    for msg in messages:
        lines.append(
            (
                f"- Mailbox: {msg.mailbox_name} ({msg.mailbox_address}) | "
                f"ID: {msg.message_id} | "
                f"From: {msg.sender} | "
                f"Date: {msg.date} | "
                f"Subject: {msg.subject}"
            )
        )
    return "\n".join(lines)


def build_prompt(soul: str, messages: list[InboxMessage], user_request: str) -> str:
    return (
        "SOUL.md:\n"
        f"{soul}\n\n"
        "Current inbox messages:\n"
        f"{format_messages_for_prompt(messages)}\n\n"
        "## Tooling\n"
        f"{TOOL_SPEC}\n\n"
        "## User request\n"
        f"{user_request}"
    )


def main() -> int:
    args = parse_args()
    try:
        mailboxes = resolve_mailboxes(args)
        soul = load_soul()
        all_messages: list[InboxMessage] = []
        for mailbox in mailboxes:
            all_messages.extend(list_inbox_messages(mailbox))
        mailboxes_by_name = {mailbox.name: mailbox for mailbox in mailboxes}

        print("\nChat ready. Type 'exit' or 'quit' to stop.")
        history: list[dict[str, str]] = []

        while True:
            try:
                user_input = input("\nPrompt> ").strip()
            except EOFError:
                print()
                return 0

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting.")
                return 0

            if not history:
                composed_prompt = build_prompt(soul, all_messages, user_input)
                if args.debug_prompt:
                    print("\n--- Composed Prompt Start ---")
                    print(composed_prompt)
                    print("--- Composed Prompt End ---")
                history.append({"role": "user", "content": composed_prompt})
            else:
                history.append({"role": "user", "content": user_input})

            tool_steps = 0
            while True:
                print(f"\nAsking {args.provider} ({args.model}) ...")
                reply = get_model_reply(
                    args.provider,
                    args.model,
                    history,
                    args.openai_api_key,
                )
                history.append({"role": "assistant", "content": reply})

                tool_requests = parse_tool_requests(reply)
                if not tool_requests:
                    print("\nModel response:")
                    print(reply)
                    break

                tool_result_lines: list[str] = []
                for i, tool_request in enumerate(tool_requests, start=1):
                    try:
                        tool_result = execute_tool_request(
                            tool_request,
                            mailboxes_by_name,
                            auto_yes=args.yes,
                        )
                    except (ValueError, RuntimeError) as exc:
                        tool_result = f"Tool execution failed: {exc}"
                    tool_result_lines.append(f"{i}. {tool_result}")

                combined_tool_result = "\n".join(tool_result_lines)
                print(f"\nTool result(s):\n{combined_tool_result}")
                history.append(
                    {
                        "role": "user",
                        "content": (
                            "Tool execution result(s):\n"
                            f"{combined_tool_result}\n\n"
                            "You may call another tool with JSON if needed, or respond to the user in plain text."
                        ),
                    }
                )
                tool_steps += 1
                if not args.noguardrail and tool_steps >= 5:
                    history.append(
                        {
                            "role": "user",
                            "content": "Stop tool calls and respond to the user in plain text now.",
                        }
                    )
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
