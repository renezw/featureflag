#!/usr/bin/env python3
"""
Simple OpenFeature Client
=========================

Einfacher Client für Feature Flag Abfragen im OpenFeature Standard.
Unterstützt Flagsmith und Unleash mit einheitlicher Ausgabe.

Verwendung:
python openfeature_client.py flagsmith my_cool_feature
python openfeature_client.py unleash my_cool_feature
"""

import sys
import requests
import json

def evaluate_flag(provider: str, flag_key: str) -> dict:
    """
    Evaluiert Feature Flag und gibt OpenFeature Standard Response zurück
    """
    
    # Provider Konfiguration
    configs = {
        "flagsmith": {
            "url": "http://localhost:8000/api/v1/flags/",
            "headers": {
                "X-Environment-Key": "PqfT7EkTugy9pbr7r8hqbF",
                "Content-Type": "application/json"
            }
        },
        "unleash": {
            "url": "http://localhost:4242/api/client/features",
            "headers": {
                "Authorization": "default:development.unleash-insecure-api-token",
                "Content-Type": "application/json"
            }
        }
    }
    
    if provider not in configs:
        return {
            "flagKey": flag_key,
            "value": False,
            "reason": "ERROR",
            "errorCode": "PROVIDER_NOT_FOUND"
        }
    
    config = configs[provider]
    
    try:
        # HTTP Request
        response = requests.get(config["url"], headers=config["headers"], timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Parse Response basierend auf Provider
        if provider == "flagsmith":
            return parse_flagsmith(data, flag_key)
        elif provider == "unleash":
            return parse_unleash(data, flag_key)
            
    except Exception:
        return {
            "flagKey": flag_key,
            "value": False,
            "reason": "ERROR", 
            "errorCode": "PROVIDER_NOT_READY"
        }

def parse_flagsmith(data: list, flag_key: str) -> dict:
    """Parst Flagsmith Response zu OpenFeature Standard"""
    for flag in data:
        if flag.get('feature', {}).get('name') == flag_key:
            enabled = flag.get('enabled', False)
            value = flag.get('feature_state_value')
            
            return {
                "flagKey": flag_key,
                "value": value if value is not None else enabled,
                "variant": "on" if enabled else "off",
                "reason": "TARGETING_MATCH" if enabled else "DEFAULT"
            }
    
    return {
        "flagKey": flag_key,
        "value": False,
        "reason": "ERROR",
        "errorCode": "FLAG_NOT_FOUND"
    }

def parse_unleash(data: dict, flag_key: str) -> dict:
    """Parst Unleash Response zu OpenFeature Standard"""
    features = data.get("features", [])
    
    for feature in features:
        if feature.get('name') == flag_key:
            enabled = feature.get('enabled', False)
            
            return {
                "flagKey": flag_key,
                "value": enabled,
                "variant": "enabled" if enabled else "disabled", 
                "reason": "TARGETING_MATCH" if enabled else "DISABLED"
            }
    
    return {
        "flagKey": flag_key,
        "value": False,
        "reason": "ERROR",
        "errorCode": "FLAG_NOT_FOUND"
    }

def main():
    """Hauptfunktion"""
    if len(sys.argv) != 3:
        print("Usage: python openfeature_client.py <provider> <flag_key>")
        print("Providers: flagsmith, unleash")
        print("Example: python openfeature_client.py flagsmith my_cool_feature")
        sys.exit(1)
    
    provider = sys.argv[1].lower()
    flag_key = sys.argv[2]
    
    # Flag evaluieren
    result = evaluate_flag(provider, flag_key)
    
    # OpenFeature Standard Ausgabe
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()