# Service check

Run `python3 weup.py` to check that `https://ricky.codes` responds
and that the domain for `hello@ricky.codes` has MX records configured.
Pass `--domain` and `--email` to check different targets, for example:

```sh
python3 weup.py --domain example.com --email hello@example.com
```

The email check looks up MX records for the domain in the email address. It
verifies DNS mail routing only.
The script exits with status `0` when both checks pass and `1` if either fails.
It uses Python 3 and the `dig` command.

## Scheduled monitoring on GitHub

The `Uptime check` GitHub Actions workflow runs every 10 minutes. It waits for
three consecutive failed checks before sending an outage email, sends one
recovery email when checks pass again, and sends a reminder no more than once
every 24 hours while an outage continues. Outage state is kept in the Actions
cache between runs.

To enable email alerts, add these repository **Actions secrets** in
**Settings → Secrets and variables → Actions**:

| Secret | Value |
| --- | --- |
| `ALERT_TO` | Alert recipient, such as `ricky.miller@gmail.com` |
| `SMTP_HOST` | SMTP server hostname from your email provider |
| `SMTP_USERNAME` | SMTP account username; also used as the From address |
| `SMTP_PASSWORD` | SMTP password or app password |

`SMTP_PORT` is optional and defaults to `465` (SMTP over SSL). If you use a
different port or TLS mode, update the workflow accordingly. For Gmail, use an
app password rather than your normal account password.

The defaults check `ricky.codes` and the MX records for `hello@ricky.codes`.
Optional repository **Actions variables** `CHECK_DOMAIN` and `CHECK_EMAIL` can
override those values. The workflow can also be started manually from the
Actions tab with **Run workflow**.

GitHub scheduled runs can start late during busy periods, and Actions cache
entries can eventually be evicted. If state is lost during an outage, the
three-failure threshold will cause a fresh alert. For a personal monitor this
is usually acceptable; a dedicated uptime service offers more reliable timing
and alert state.
