#!/usr/bin/env python3
"""
OpenFeature SDK Client (API korrigiert)
=======================================

Client basierend auf dem offiziellen OpenFeature Python SDK.
Korrigierte API-Verwendung für Flagsmith und Unleash.

Installation:
pip install openfeature-sdk requests

Verwendung:
python openfeature_client.py flagsmith my_cool_feature
python openfeature_client.py unleash my_cool_feature
"""

import sys
import json
import requests
from typing import List, Optional, Any, Dict
from openfeature import api
from openfeature.provider import AbstractProvider, Metadata
from openfeature.flag_evaluation import FlagResolutionDetails
from openfeature.evaluation_context import EvaluationContext

class FlagsmithProvider(AbstractProvider):
    """OpenFeature Provider für Flagsmith"""
    
    def __init__(self, environment_key: str, api_url: str = "http://localhost:8000"):
        self.environment_key = environment_key
        self.api_url = api_url.rstrip('/')
        self._metadata = Metadata("flagsmith-provider")
    
    def get_metadata(self) -> Metadata:
        return self._metadata
    
    def _fetch_flags(self) -> Optional[List[Dict]]:
        """Holt alle Flags von Flagsmith API"""
        try:
            url = f"{self.api_url}/api/v1/flags/"
            headers = {
                "X-Environment-Key": self.environment_key,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
    
    def _convert_value(self, raw_value: Any, target_type: type, enabled: bool):
        """Konvertiert Raw-Wert zu Ziel-Typ"""
        if raw_value is None:
            # Fallback auf enabled für boolean, sonst None
            if target_type == bool:
                return enabled
            return None
        
        try:
            if target_type == bool:
                if isinstance(raw_value, bool):
                    return raw_value
                elif isinstance(raw_value, str):
                    return raw_value.lower() in ('true', '1', 'yes', 'on')
                else:
                    return bool(raw_value)
            
            elif target_type == str:
                return str(raw_value)
            
            elif target_type == int:
                return int(raw_value)
            
            elif target_type == float:
                return float(raw_value)
            
            elif target_type == dict:
                if isinstance(raw_value, dict):
                    return raw_value
                else:
                    return json.loads(raw_value)
            
            return raw_value
            
        except (ValueError, TypeError, json.JSONDecodeError):
            return None
    
    def _resolve_flag_generic(self, flag_key: str, default_value: Any, target_type: type) -> FlagResolutionDetails:
        """Generische Flag-Resolution"""
        flags = self._fetch_flags()
        
        if flags is None:
            return FlagResolutionDetails(
                value=default_value,
                reason="ERROR",
                error_code="PROVIDER_NOT_READY"
            )
        
        # Flag suchen
        for flag in flags:
            if flag.get('feature', {}).get('name') == flag_key:
                enabled = flag.get('enabled', False)
                raw_value = flag.get('feature_state_value')
                
                # Wert konvertieren
                converted_value = self._convert_value(raw_value, target_type, enabled)
                
                if converted_value is not None:
                    return FlagResolutionDetails(
                        value=converted_value,
                        reason="TARGETING_MATCH" if enabled else "DEFAULT",
                        variant="on" if enabled else "off"
                    )
                else:
                    return FlagResolutionDetails(
                        value=default_value,
                        reason="DEFAULT",
                        variant="off"
                    )
        
        # Flag nicht gefunden
        return FlagResolutionDetails(
            value=default_value,
            reason="DEFAULT",
            error_code="FLAG_NOT_FOUND"
        )
    
    def resolve_boolean_details(self, flag_key: str, default_value: bool, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[bool]:
        """Resolve boolean flag from Flagsmith"""
        return self._resolve_flag_generic(flag_key, default_value, bool)
    
    def resolve_string_details(self, flag_key: str, default_value: str, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[str]:
        """Resolve string flag from Flagsmith"""
        return self._resolve_flag_generic(flag_key, default_value, str)
    
    def resolve_integer_details(self, flag_key: str, default_value: int, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[int]:
        """Resolve integer flag from Flagsmith"""
        return self._resolve_flag_generic(flag_key, default_value, int)
    
    def resolve_float_details(self, flag_key: str, default_value: float, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[float]:
        """Resolve float flag from Flagsmith"""
        return self._resolve_flag_generic(flag_key, default_value, float)
    
    def resolve_object_details(self, flag_key: str, default_value: dict, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[dict]:
        """Resolve object flag from Flagsmith"""
        return self._resolve_flag_generic(flag_key, default_value, dict)

class UnleashProvider(AbstractProvider):
    """OpenFeature Provider für Unleash"""
    
    def __init__(self, auth_token: str, api_url: str = "http://localhost:4242"):
        self.auth_token = auth_token
        self.api_url = api_url.rstrip('/')
        self._metadata = Metadata("unleash-provider")
    
    def get_metadata(self) -> Metadata:
        return self._metadata
    
    def _fetch_features(self) -> Optional[List[Dict]]:
        """Holt alle Features von Unleash API"""
        try:
            url = f"{self.api_url}/api/client/features"
            headers = {
                "Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("features", [])
        except Exception:
            return None
    
    def _convert_value(self, enabled: bool, target_type: type):
        """Konvertiert boolean zu Ziel-Typ (Unleash ist hauptsächlich boolean-basiert)"""
        try:
            if target_type == bool:
                return enabled
            elif target_type == str:
                return str(enabled)
            elif target_type == int:
                return 1 if enabled else 0
            elif target_type == float:
                return 1.0 if enabled else 0.0
            elif target_type == dict:
                return {"enabled": enabled}
            return enabled
        except Exception:
            return None
    
    def _resolve_flag_generic(self, flag_key: str, default_value: Any, target_type: type) -> FlagResolutionDetails:
        """Generische Flag-Resolution für Unleash"""
        features = self._fetch_features()
        
        if features is None:
            return FlagResolutionDetails(
                value=default_value,
                reason="ERROR",
                error_code="PROVIDER_NOT_READY"
            )
        
        # Feature suchen
        for feature in features:
            if feature.get('name') == flag_key:
                enabled = feature.get('enabled', False)
                converted_value = self._convert_value(enabled, target_type)
                
                return FlagResolutionDetails(
                    value=converted_value,
                    reason="TARGETING_MATCH" if enabled else "DISABLED",
                    variant="enabled" if enabled else "disabled"
                )
        
        # Feature nicht gefunden
        return FlagResolutionDetails(
            value=default_value,
            reason="DEFAULT",
            error_code="FLAG_NOT_FOUND"
        )
    
    def resolve_boolean_details(self, flag_key: str, default_value: bool, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[bool]:
        """Resolve boolean flag from Unleash"""
        return self._resolve_flag_generic(flag_key, default_value, bool)
    
    def resolve_string_details(self, flag_key: str, default_value: str, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[str]:
        """Resolve string flag from Unleash"""
        return self._resolve_flag_generic(flag_key, default_value, str)
    
    def resolve_integer_details(self, flag_key: str, default_value: int, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[int]:
        """Resolve integer flag from Unleash"""
        return self._resolve_flag_generic(flag_key, default_value, int)
    
    def resolve_float_details(self, flag_key: str, default_value: float, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[float]:
        """Resolve float flag from Unleash"""
        return self._resolve_flag_generic(flag_key, default_value, float)
    
    def resolve_object_details(self, flag_key: str, default_value: dict, context: Optional[EvaluationContext] = None) -> FlagResolutionDetails[dict]:
        """Resolve object flag from Unleash"""
        return self._resolve_flag_generic(flag_key, default_value, dict)

def evaluate_flag_with_sdk(provider_name: str, flag_key: str, flag_type: str = "boolean", default_value: Any = False):
    """Evaluiert Flag mit OpenFeature SDK - direkte Provider-Verwendung"""
    
    # Provider erstellen
    if provider_name == "flagsmith":
        provider = FlagsmithProvider(
            environment_key="PqfT7EkTugy9pbr7r8hqbF",
            api_url="http://localhost:8000"
        )
    elif provider_name == "unleash":
        provider = UnleashProvider(
            auth_token="default:development.unleash-insecure-api-token",
            api_url="http://localhost:4242"
        )
    else:
        return {
            "flagKey": flag_key,
            "value": default_value,
            "reason": "ERROR",
            "errorCode": "PROVIDER_NOT_FOUND"
        }
    
    # Flag direkt vom Provider evaluieren
    try:
        if flag_type == "boolean":
            result = provider.resolve_boolean_details(flag_key, default_value or False)
        elif flag_type == "string":
            result = provider.resolve_string_details(flag_key, default_value or "")
        elif flag_type == "integer":
            result = provider.resolve_integer_details(flag_key, default_value or 0)
        elif flag_type == "float":
            result = provider.resolve_float_details(flag_key, default_value or 0.0)
        elif flag_type == "object":
            result = provider.resolve_object_details(flag_key, default_value or {})
        else:
            result = provider.resolve_boolean_details(flag_key, False)
        
        # OpenFeature Standard Response
        response = {
            "flagKey": flag_key,
            "value": result.value,
            "reason": result.reason
        }
        
        if result.variant:
            response["variant"] = result.variant
        
        if result.error_code:
            response["errorCode"] = result.error_code
        
        if result.error_message:
            response["errorMessage"] = result.error_message
        
        return response
        
    except Exception as e:
        return {
            "flagKey": flag_key,
            "value": default_value,
            "reason": "ERROR",
            "errorCode": "GENERAL",
            "errorMessage": str(e)
        }

def main():
    """Hauptfunktion"""
    if len(sys.argv) < 3:
        print("Usage: python openfeature_client.py <provider> <flag_key> [flag_type] [default_value]")
        print("Providers: flagsmith, unleash")
        print("Flag types: boolean, string, integer, float, object")
        print("Examples:")
        print("  python openfeature_client.py flagsmith my_cool_feature")
        print("  python openfeature_client.py unleash my_cool_feature boolean")
        print("  python openfeature_client.py flagsmith welcome_message string 'Hello World'")
        sys.exit(1)
    
    provider = sys.argv[1].lower()
    flag_key = sys.argv[2]
    flag_type = sys.argv[3] if len(sys.argv) > 3 else "boolean"
    default_value = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Default value basierend auf Typ
    if default_value is None:
        defaults = {
            "boolean": False,
            "string": "",
            "integer": 0,
            "float": 0.0,
            "object": {}
        }
        default_value = defaults.get(flag_type, False)
    else:
        # Typ-Konvertierung
        if flag_type == "boolean":
            default_value = default_value.lower() in ('true', '1', 'yes')
        elif flag_type == "integer":
            default_value = int(default_value)
        elif flag_type == "float":
            default_value = float(default_value)
        elif flag_type == "object":
            default_value = json.loads(default_value)
    
    # Flag mit OpenFeature SDK evaluieren
    result = evaluate_flag_with_sdk(provider, flag_key, flag_type, default_value)
    
    # OpenFeature Standard Ausgabe
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()