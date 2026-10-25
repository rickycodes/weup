#!/usr/bin/env python3
"""Run service checks and send deduplicated outage and recovery emails."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import json
import os
from pathlib import Path
import smtplib
import ssl
import sys

from weup import check_email_route, check_website

FAILURES_BEFORE_ALERT = 3
REMINDER_AFTER = timedelta(hours=24)


def now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def send_alert(subject: str, body: str) -> None:
    required = ["ALERT_TO", "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing alert configuration: " + ", ".join(missing))

    message = EmailMessage()
    message["From"] = os.environ["SMTP_USERNAME"]
    message["To"] = os.environ["ALERT_TO"]
    message["Subject"] = subject
    message.set_content(body)

    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(
        os.environ["SMTP_HOST"], port, context=ssl.create_default_context(), timeout=15
    ) as smtp:
        smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default=os.environ.get("CHECK_DOMAIN", "ricky.codes"))
    parser.add_argument("--email", default=os.environ.get("CHECK_EMAIL", "hello@ricky.codes"))
    parser.add_argument("--state-file", type=Path, default=Path(".uptime-state/state.json"))
    args = parser.parse_args()

    website_ok = check_website(args.domain)
    email_ok = check_email_route(args.email)
    healthy = website_ok and email_ok

    args.state_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        state = json.loads(args.state_file.read_text())
    except FileNotFoundError:
        state = {}

    previous_status = state.get("status", "up")
    failures = 0 if healthy else int(state.get("consecutive_failures", 0)) + 1
    current_time = now()
    last_alert = parse_time(state.get("last_alert_at"))
    notification = None

    if healthy:
        if previous_status == "down" and state.get("alert_sent"):
            duration = current_time - (parse_time(state.get("outage_started_at")) or current_time)
            notification = (
                f"[weup] Recovered: {args.domain}",
                f"Checks for {args.domain} and {args.email} are passing again.\n"
                f"Outage duration: {duration}.",
            )
        state = {"status": "up", "consecutive_failures": 0}
    else:
        if previous_status != "down":
            state["outage_started_at"] = current_time.isoformat()
            state["alert_sent"] = False
            last_alert = None
        if failures >= FAILURES_BEFORE_ALERT:
            should_alert = not state.get("alert_sent") or (
                last_alert is not None and current_time - last_alert >= REMINDER_AFTER
            )
            if should_alert:
                kind = "Outage" if not state.get("alert_sent") else "Still down"
                notification = (
                    f"[weup] {kind}: {args.domain}",
                    f"One or more checks are failing for {args.domain} / {args.email}.\n"
                    f"Consecutive failed checks: {failures}.\n"
                    "See the GitHub Actions run for the check output.",
                )
        state.update({"status": "down", "consecutive_failures": failures})

    if notification:
        send_alert(*notification)
        state["alert_sent"] = not healthy
        state["last_alert_at"] = current_time.isoformat()
        print(f"Notification sent: {notification[0]}")

    args.state_file.write_text(json.dumps(state, indent=2) + "\n")
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
