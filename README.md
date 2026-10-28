# WeUp

WeUp checks that a website responds over HTTPS and that the domain used by an
email address has MX records. The email check verifies DNS mail routing only;
it does not connect to an SMTP server or confirm mailbox delivery.

## Use as a GitHub Action

Add a workflow to your repository and set the targets:

```yaml
name: Uptime check
on:
  schedule:
    - cron: "*/10 * * * *"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: uptime-check
  cancel-in-progress: false

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: rickycodes/weup@v1
        with:
          domain: example.com
          email: hello@example.com
          alert-to: ${{ secrets.ALERT_TO }}
          smtp-host: ${{ secrets.SMTP_HOST }}
          smtp-username: ${{ secrets.SMTP_USERNAME }}
          smtp-password: ${{ secrets.SMTP_PASSWORD }}
```

Pin the action to a release tag (such as `@v1`) or a commit SHA. Set `domain`,
`email`, or both. At least one is required. Run the action on an Ubuntu/Linux
runner with `sudo` and `apt-get`. It installs Python and `dnsutils` on the
runner.

To check only a website, provide `domain` and omit `email`. To check only mail
routing, provide `email` and omit `domain`.

Email alert inputs are optional. With `alert-to` omitted, the action runs the
check directly and fails the step if any selected check fails. When `alert-to` is
set, provide `smtp-host`, `smtp-username`, and `smtp-password`; `smtp-port`
defaults to `465`. Alert settings are validated before checks begin. It sends
an outage alert after three consecutive failing runs, reminders at most once
every 24 hours, and one recovery alert when checks pass again. Store SMTP
credentials and the recipient as repository or organization Actions secrets.
For Gmail, use an app password.

Alert state is stored in the Actions cache under `.weup-state`. Cache entries
can be evicted, and scheduled GitHub Actions runs may start late during busy
periods. After state loss, the three-failure threshold starts over.

## Run locally

```sh
python3 weup.py --domain example.com --email hello@example.com
```

The local check requires Python 3 and the `dig` command. It exits with status
`0` when both checks pass and `1` if either fails.
