import json
import os
from pathlib import Path
from typing import Dict, Any, List
import jsonschema
from jsonschema import validate, Draft7Validator
from jsonschema.exceptions import ValidationError
from utils.logger import logger


class SchemaValidator:
    """JSON schema validator"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchemaValidator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.validator = Draft7Validator
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._errors: List[Dict[str, Any]] = []
        self._initialized = True
        
        # Register custom formats
        self._register_custom_formats()
    
    def _register_custom_formats(self):
        """Register custom JSON schema formats"""
        # These would be registered with a custom validator
        # For now, we'll handle them in validation
        pass
    
    def load_schema(self, schema_type: str, schema_name: str) -> Dict[str, Any]:
        """
        Load schema from file
        
        Args:
            schema_type: Type of schema (e.g., 'articles', 'tags')
            schema_name: Name of schema file
            
        Returns:
            Schema dictionary
        """
        cache_key = f"{schema_type}/{schema_name}"
        
        if cache_key in self._schemas:
            return self._schemas[cache_key]
        
        schema_path = Path(__file__).parent.parent / "response_schemas" / schema_type / f"{schema_name}.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        self._schemas[cache_key] = schema
        return schema
    
    def validate(self, data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against schema
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Returns:
            True if valid
        """
        self._errors.clear()
        
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            self._errors.append({
                "path": list(e.path),
                "message": e.message,
                "validator": e.validator,
                "validator_value": e.validator_value
            })
            return False
        except Exception as e:
            self._errors.append({
                "message": str(e)
            })
            return False
    
    async def validate_response(self, response, schema_type: str, schema_name: str) -> bool:
        """
        Validate response against schema
        
        Args:
            response: API response
            schema_type: Type of schema
            schema_name: Name of schema file
            
        Returns:
            True if valid
        """
        try:
            data = await response.json()
            schema = self.load_schema(schema_type, schema_name)
            return self.validate(data, schema)
        except Exception as e:
            logger.error(f"Failed to validate response: {str(e)}")
            return False
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Get validation errors"""
        return self._errors.copy()
    
    def clear_errors(self):
        """Clear validation errors"""
        self._errors.clear()
    
    def create_article_schema(self) -> Dict[str, Any]:
        """Create article response schema"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["article"],
            "properties": {
                "article": {
                    "type": "object",
                    "required": ["slug", "title", "description", "body", "createdAt", "updatedAt", "favorited", "favoritesCount", "author"],
                    "properties": {
                        "slug": {
                            "type": "string",
                            "pattern": "^.*?(\\d{1,3}\\.[A-Z]{2}\\.\\d{4})$|^(\\d{4}\\.\\d{2}\\.\\d{4})$"
                        },
                        "title": {"type": "string", "minLength": 1},
                        "description": {"type": "string"},
                        "body": {"type": "string"},
                        "tagList": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "createdAt": {"type": "string", "format": "date-time"},
                        "updatedAt": {"type": "string", "format": "date-time"},
                        "favorited": {"type": "boolean"},
                        "favoritesCount": {"type": "integer", "minimum": 0},
                        "author": {
                            "type": "object",
                            "required": ["username", "bio", "image", "following"],
                            "properties": {
                                "username": {"type": "string"},
                                "bio": {"type": ["string", "null"]},
                                "image": {"type": ["string", "null"], "format": "uri"},
                                "following": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
    
    def create_paginated_schema(self, item_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create paginated response schema"""
        return {
            "type": "object",
            "required": ["items", "total", "page", "per_page", "total_pages"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": item_schema
                },
                "total": {"type": "integer", "minimum": 0},
                "page": {"type": "integer", "minimum": 1},
                "per_page": {"type": "integer", "minimum": 1},
                "total_pages": {"type": "integer", "minimum": 0}
            }
        }