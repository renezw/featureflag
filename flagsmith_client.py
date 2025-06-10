import os
import requests


def get_flag(flag_name, default=False):
    """Return the boolean value of a feature flag from Flagsmith."""
    base_url = os.getenv("FLAGSMITH_URL", "http://localhost:8000")
    env_key = os.getenv("FLAGSMITH_ENVIRONMENT_KEY")
    headers = {}
    if env_key:
        headers["X-Environment-Key"] = env_key

    response = requests.get(f"{base_url}/api/v1/flags/", headers=headers)
    response.raise_for_status()

    for flag in response.json():
        if flag.get("feature", {}).get("name") == flag_name:
            return flag.get("enabled", default)
    return default


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Query a Flagsmith flag")
    parser.add_argument("flag", help="Name of the flag to query")
    parser.add_argument("--default", dest="default", action="store_true",
                        help="Default value if flag is not found or request fails")

    args = parser.parse_args()
    try:
        enabled = get_flag(args.flag, args.default)
        print(enabled)
    except Exception as exc:
        print(args.default)


if __name__ == "__main__":
    main()
