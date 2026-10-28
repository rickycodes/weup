#!/usr/bin/env python3
"""Check HTTPS and mail routing configuration for a website and email address.

The email check looks up the domain's MX records. It does not connect to an
SMTP server or send a message, so it cannot confirm delivery to the mailbox.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.error
import urllib.request

TIMEOUT = 4


def check_website(domain: str) -> bool:
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(f"https://{domain}/", method=method)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                print(f"website ({domain}): UP (HTTPS {response.status}, {method})")
                return 200 <= response.status < 400
        except urllib.error.HTTPError as error:
            if method == "HEAD" and error.code in (405, 501):
                error.close()
                continue
            # An HTTP response, including 4xx/5xx, means the server was reached.
            print(f"website ({domain}): DOWN (HTTPS {error.code})")
        except Exception as error:
            print(f"website ({domain}): DOWN ({error})")
        return False
    return False


def lookup_mx(domain: str) -> list[str]:
    result = subprocess.run(
        ["dig", "+short", "MX", domain],
        check=False,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "dig failed")
    records = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            records.append((int(parts[0]), parts[1].rstrip(".")))
    return [host for _, host in sorted(records)]


def check_email_route(email: str) -> bool:
    _, separator, mail_domain = email.rpartition("@")
    if not separator or not mail_domain or "@" in mail_domain:
        print(f"email ({email}): DOWN (invalid email address)")
        return False
    try:
        hosts = lookup_mx(mail_domain)
        if not hosts:
            print(f"email ({email}): DOWN (no MX records for {mail_domain})")
            return False
        print(f"email ({email}): ROUTED (MX records: {', '.join(hosts)})")
        return True
    except Exception as error:
        print(f"email ({email}): DOWN ({error})")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check website HTTPS and email-domain MX records.")
    parser.add_argument("--domain", help="website domain to check")
    parser.add_argument(
        "--email",
        help="email address whose domain's MX records are checked",
    )
    args = parser.parse_args()

    if not args.domain and not args.email:
        parser.error("provide at least one of --domain or --email")

    results = []
    if args.domain:
        results.append(check_website(args.domain))
    if args.email:
        results.append(check_email_route(args.email))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
