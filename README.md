# OVH DynHost Updater

A small Python script that keeps one or more OVH DynHost records pointed at your current public IPv4 address. It is meant to run periodically, for example every few minutes, on a machine behind a dynamic IP.

## How it works

1. The script fetches the current public IP from [ipify](https://www.ipify.org/).
2. For each hostname, it reads the existing `A` record directly from the zone's authoritative nameserver. This bypasses local DNS caches, so a recent change is seen immediately.
3. If the record already matches, nothing is sent to OVH.
4. Otherwise, it calls OVH's DynDNS endpoint. The update counts as successful only if OVH replies with `good` or `nochg`.
5. When every host is done, it optionally sends a single ping to [Healthchecks.io](https://healthchecks.io/). That ping goes to `/fail` if any host failed or a network error occurred.

## Requirements

- Python 3.8 or newer
- A DynHost record and DynHost credentials, both created in the OVH control panel. Go to **Web Cloud → Domains → your domain → DynHost**, create the record, then use **Manage access** to create a login.

## Installation

```bash
python -m pip install requests dnspython python-decouple
```

> **Note:** install `python-decouple`, **not** `decouple`. They are two different packages that both import as `decouple`. Only `python-decouple` provides `config`. If you get `ImportError: cannot import name 'config' from 'decouple'`, see [Troubleshooting](#troubleshooting).

## Configuration

Create a `.env` file in the same directory as `main.py`:

```ini
OVH-USERNAME=yourdomain.ch-dynhost
OVH-PASSWORD=your-dynhost-password

# Optional: Healthchecks.io ping URL
HEALTHCHECK-URL=https://hc-ping.com/your-check-uuid
```

| Variable          | Required | Description                                                      |
|-------------------|----------|------------------------------------------------------------------|
| `OVH-USERNAME`    | yes      | DynHost login created under *Manage access*                      |
| `OVH-PASSWORD`    | yes      | Password for that login                                          |
| `HEALTHCHECK-URL` | no       | Healthchecks.io ping URL. If omitted, no ping is sent.           |

The script also reads these values from environment variables, which take precedence over `.env`. Keep `.env` out of version control:

```bash
echo ".env" >> .gitignore
```

## Usage

```bash
python main.py host.example.com
python main.py host1.example.com host2.example.com
```

Example output:

```
[OK] host1.example.com già aggiornato (203.0.113.42)
[UPDATED] host2.example.com: 198.51.100.7 -> 203.0.113.42 (good 203.0.113.42)
```

### Exit codes

| Code | Meaning                                       |
|------|-----------------------------------------------|
| `0`  | All hosts up to date or updated successfully  |
| `1`  | At least one host failed, or a network error  |
| `2`  | No hostnames given on the command line        |

## Scheduling

### Windows (Task Scheduler)

To run the script every 5 minutes:

```powershell
schtasks /Create /TN "OVH DynHost" /SC MINUTE /MO 5 `
  /TR "python C:\path\to\dynhost\main.py host.example.com"
```

If `python` isn't on the `PATH` of the account running the task, use the full path to `python.exe`. You can find it with `where.exe python`. A non-zero exit code shows up as a failed run in the task history.

### Linux / macOS (cron)

```cron
*/5 * * * * /usr/bin/python3 /path/to/dynhost/main.py host.example.com >> /var/log/dynhost.log 2>&1
```

### Healthchecks.io

Set the check's period to match your schedule, for example 5 minutes, and give it a grace time of a few periods. You'll get an alert if the script stops running entirely or reports a failure.

## Troubleshooting

**`ImportError: cannot import name 'config' from 'decouple'`**
The wrong package is installed. Remove both packages and reinstall the right one:

```bash
python -m pip uninstall -y decouple python-decouple
python -m pip install python-decouple
```

Use `python -m pip` rather than `pip`, so the package is installed into the same interpreter that runs the script.

**`decouple.UndefinedValueError: OVH-USERNAME not found`**
The `.env` file is missing, isn't next to `main.py`, or misspells the variable name.

**`[ERRORE] ... HTTP 401 - badauth`**
Wrong DynHost credentials. These are the logins created under *DynHost → Manage access*, **not** your OVH account login.

**`[ERRORE] ... nohost`**
The hostname doesn't exist as a DynHost record, or the login isn't authorized for that subdomain.

**The script updates on every run**
Check that the machine can reach the domain's authoritative nameservers on port 53. If the authoritative lookup fails, the script falls back to sending an update. That's harmless (OVH answers `nochg`), but it does create unnecessary requests.

## Limitations

- IPv4 only (`A` records). IPv6 / `AAAA` records are not handled.
- All hosts are set to the same IP, the public address of the machine running the script.
