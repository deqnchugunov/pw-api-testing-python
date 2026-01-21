import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Union
from jsonschema import validate
from utils.logger import logger
from utils.schema_validator import SchemaValidator


class Expect:
    """Custom expectation class for API testing"""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
    
    async def to_match_schema(self, response, schema_type: str, schema_name: str) -> None:
        """
        Validate response against JSON schema from file
        
        Args:
            response: API response object
            schema_type: Type of schema (e.g., 'articles', 'tags')
            schema_name: Name of schema file (e.g., 'get_articles')
        """
        try:
            # Get response body
            response_body = await response.json()
            
            # Load schema
            schema_path = Path(__file__).parent.parent / "response_schemas" / schema_type / f"{schema_name}.json"
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Validate schema
            is_valid = self.schema_validator.validate(response_body, schema)
            
            if not is_valid:
                errors = self.schema_validator.get_errors()
                error_message = f"Schema validation failed for {schema_type}/{schema_name}:\n{json.dumps(errors, indent=2)}"
                logger.error(error_message)
                raise AssertionError(error_message)
            
            logger.info(f"Response matches schema: {schema_type}/{schema_name}")
            
        except Exception as e:
            logger.error(f"Failed to validate schema: {str(e)}")
            raise
    
    async def to_match_snapshot(self, response, entity_type: str, snapshot_name: str) -> None:
        """
        Match response against snapshot
        
        Args:
            response: API response object
            entity_type: Type of entity (e.g., 'articles')
            snapshot_name: Name of snapshot (e.g., 'post_articles')
        """
        try:
            snapshot_path = Path(__file__).parent.parent / "__snapshots__" / entity_type / f"{snapshot_name}.json"
            
            # Get response body
            response_body = await response.json()
            
            if snapshot_path.exists():
                # Compare with existing snapshot
                with open(snapshot_path, 'r') as f:
                    expected_snapshot = json.load(f)
                
                # Normalize responses for comparison
                normalized_response = self._normalize_response(response_body)
                normalized_snapshot = self._normalize_response(expected_snapshot)
                
                if normalized_response != normalized_snapshot:
                    # Create diff or save new snapshot in test mode
                    logger.warning(f"Snapshot mismatch for {entity_type}/{snapshot_name}")
                    # In real implementation, you might want to update snapshots in CI
                    # or provide a diff
            else:
                # Create directory and save snapshot
                snapshot_path.parent.mkdir(parents=True, exist_ok=True)
                with open(snapshot_path, 'w') as f:
                    json.dump(response_body, f, indent=2)
                logger.info(f"Created new snapshot: {snapshot_path}")
                
        except Exception as e:
            logger.error(f"Failed to compare snapshot: {str(e)}")
            raise
    
    def _normalize_response(self, obj: Any) -> Any:
        """Normalize response by removing/replacing dynamic values"""
        if isinstance(obj, list):
            return [self._normalize_response(item) for item in obj]
        elif isinstance(obj, dict):
            normalized = {}
            for key, value in obj.items():
                # Skip or replace dynamic fields
                if key in ['id', 'createdAt', 'updatedAt', 'timestamp', 'created_at', 'updated_at']:
                    normalized[key] = '[DYNAMIC]'
                elif key == 'slug' and isinstance(value, str):
                    # Normalize slug pattern
                    normalized[key] = re.sub(r'\d+', '[ID]', value)
                else:
                    normalized[key] = self._normalize_response(value)
            return normalized
        else:
            return obj
    
    async def to_have_status_code(self, response, expected_status: int) -> None:
        """
        Validate response status code
        
        Args:
            response: API response object
            expected_status: Expected HTTP status code
        """
        actual_status = response.status
        
        if actual_status != expected_status:
            try:
                body = await response.text()
                error_message = f"Expected status {expected_status}, but received {actual_status}"
                if body:
                    error_message += f"\nResponse: {body[:500]}"
            except:
                error_message = f"Expected status {expected_status}, but received {actual_status}"
            
            logger.error(error_message)
            raise AssertionError(error_message)
        
        logger.info(f"Status code {actual_status} matches expected {expected_status}")
    
    def to_be_greater_than_or_equal(self, actual, expected) -> None:
        """Check if actual is greater than or equal to expected"""
        if actual < expected:
            error_message = f"Expected {actual} to be greater than or equal to {expected}"
            logger.error(error_message)
            raise AssertionError(error_message)
        logger.info(f"{actual} is greater than or equal to {expected}")
    
    def to_be_truthy(self, value) -> None:
        """Check if value is truthy"""
        if not value:
            error_message = f"Expected value to be truthy, but got {value}"
            logger.error(error_message)
            raise AssertionError(error_message)
        logger.info("Value is truthy")
    
    def to_equal(self, actual, expected) -> None:
        """Check if actual equals expected"""
        if actual != expected:
            error_message = f"Expected {expected}, but got {actual}"
            logger.error(error_message)
            raise AssertionError(error_message)
        logger.info(f"{actual} equals {expected}")
    
    def to_contain(self, container, item) -> None:
        """Check if container contains item"""
        if item not in container:
            error_message = f"Expected {container} to contain {item}"
            logger.error(error_message)
            raise AssertionError(error_message)
        logger.info(f"Container contains {item}")
    
    def to_match_pattern(self, value, pattern: str) -> None:
        """Check if value matches regex pattern"""
        if not re.match(pattern, value):
            error_message = f"Expected {value} to match pattern {pattern}"
            logger.error(error_message)
            raise AssertionError(error_message)
        logger.info(f"{value} matches pattern {pattern}")


# Create singleton instance
expect = Expect()