# featureflag

Minimal Python client for querying a flag from a Flagsmith server.

## Requirements

- Python 3.8+
- [`requests`](https://pypi.org/project/requests/) library

## Usage

1. Set the environment variable `FLAGSMITH_ENVIRONMENT_KEY` to your Flagsmith environment key.
2. Optionally set `FLAGSMITH_URL` if the server is not at `http://localhost:8000`.
3. Run the client to check a flag:

```bash
python flagsmith_client.py my_flag_name
```

The script will print `True` or `False` depending on whether the flag is enabled.
