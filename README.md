# OVH_DynHost
A small Python script to update OVH DNS records (type A) dynamically.

## Installation
1. Install following dependencies:
   `pip install dnspython decouple`
2. Open the `.env` file and update `OVH-USERNAME` and `OVH-PASSWORD` with the credentials of the DynHost account (you can create them into your OVH Control Panel > Domains > example.com > DynHost tab)
3. Run the script passing one or more domain names you want to update: `python main.py example.com`
4. Check that it works and schedule a cronjob (every 5 mins): `*/5 * * * * /path/to/script/main.py`
