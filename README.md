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
