"""
TOON (Token-Oriented Object Notation) encoder/decoder
Based on TOON spec v2.0
"""
import json
import yaml
from typing import Any, Union


class TOONEncoder:
    """Encodes Python objects to TOON format"""
    
    def __init__(self, indent_size: int = 2):
        self.indent_size = indent_size
    
    def encode(self, data: Any, indent: int = 0) -> str:
        """Convert Python object to TOON string"""
        if data is None:
            return "null"
        elif isinstance(data, bool):
            return "true" if data else "false"
        elif isinstance(data, (int, float)):
            return str(data)
        elif isinstance(data, str):
            return self._encode_string(data)
        elif isinstance(data, list):
            return self._encode_array(data, indent)
        elif isinstance(data, dict):
            return self._encode_object(data, indent)
        else:
            return str(data)
    
    def _encode_string(self, s: str) -> str:
        """Encode string with quotes if needed"""
        # Need quotes if contains comma, colon, newline, or starts with special chars
        needs_quotes = any(c in s for c in [',', ':', '\n', '\r']) or \
                      s.startswith(('#', '-', '[', '{')) or \
                      s in ['null', 'true', 'false'] or \
                      s.strip() == ''
        
        if needs_quotes:
            # Escape quotes and backslashes
            escaped = s.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        return s
    
    def _is_uniform_array_of_objects(self, arr: list) -> tuple[bool, list]:
        """Check if array is uniform objects and return fields"""
        if not arr or not all(isinstance(item, dict) for item in arr):
            return False, []
        
        # Get fields from first object
        first_keys = list(arr[0].keys())
        
        # Check all objects have same keys and all values are primitives
        for item in arr:
            if list(item.keys()) != first_keys:
                return False, []
            if not all(isinstance(v, (str, int, float, bool, type(None))) for v in item.values()):
                return False, []
        
        return True, first_keys
    
    def _encode_array(self, arr: list, indent: int) -> str:
        """Encode array in TOON format"""
        if not arr:
            return "[]"
        
        # Check if it's a uniform array of objects (tabular format)
        is_uniform, fields = self._is_uniform_array_of_objects(arr)
        
        if is_uniform:
            # Use tabular format
            result = []
            fields_str = ','.join(fields)
            result.append(f"[{len(arr)}]{{{fields_str}}}:")
            
            indent_str = ' ' * (indent + self.indent_size)
            for item in arr:
                values = [self._encode_primitive(item[field]) for field in fields]
                result.append(indent_str + ','.join(values))
            
            return '\n'.join(result)
        else:
            # Use list format with dashes
            result = []
            result.append(f"[{len(arr)}]:")
            
            indent_str = ' ' * (indent + self.indent_size)
            for item in arr:
                if isinstance(item, (dict, list)):
                    item_str = self.encode(item, indent + self.indent_size)
                    if '\n' in item_str:
                        result.append(indent_str + "- " + item_str.replace('\n', '\n' + indent_str + '  '))
                    else:
                        result.append(indent_str + "- " + item_str)
                else:
                    result.append(indent_str + "- " + self._encode_primitive(item))
            
            return '\n'.join(result)
    
    def _encode_primitive(self, value: Any) -> str:
        """Encode primitive value"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return self._encode_string(str(value))
    
    def _encode_object(self, obj: dict, indent: int) -> str:
        """Encode object in TOON format"""
        if not obj:
            return "{}"
        
        result = []
        indent_str = ' ' * indent
        next_indent_str = ' ' * (indent + self.indent_size)
        
        for key, value in obj.items():
            if isinstance(value, dict):
                # Nested object
                nested = self._encode_object(value, indent + self.indent_size)
                if '\n' in nested:
                    result.append(f"{next_indent_str}{key}:")
                    result.append(nested)
                else:
                    result.append(f"{next_indent_str}{key}: {nested}")
            elif isinstance(value, list):
                # Array
                is_uniform, fields = self._is_uniform_array_of_objects(value)
                if is_uniform and value:
                    # Tabular array
                    fields_str = ','.join(fields)
                    result.append(f"{next_indent_str}{key}[{len(value)}]{{{fields_str}}}:")
                    
                    table_indent_str = ' ' * (indent + self.indent_size * 2)
                    for item in value:
                        values = [self._encode_primitive(item[field]) for field in fields]
                        result.append(table_indent_str + ','.join(values))
                else:
                    # Regular array
                    array_str = self._encode_array(value, indent + self.indent_size)
                    if '\n' in array_str:
                        result.append(f"{next_indent_str}{key}{array_str[array_str.index('['):]}")
                    else:
                        result.append(f"{next_indent_str}{key}: {array_str}")
            else:
                # Primitive value
                result.append(f"{next_indent_str}{key}: {self._encode_primitive(value)}")
        
        return '\n'.join(result)


def json_to_toon(json_str: str) -> str:
    """Convert JSON string to TOON format"""
    try:
        data = json.loads(json_str)
        encoder = TOONEncoder()
        return encoder.encode(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def json_to_yaml(json_str: str) -> str:
    """Convert JSON string to YAML format"""
    try:
        data = json.loads(json_str)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (GPT tokenizer)"""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("o200k_base")  # GPT-4o/GPT-5 tokenizer
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimation
        return len(text) // 4


# Example usage and tests
if __name__ == "__main__":
    # Example 1: Simple users
    data1 = {
        "users": [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"}
        ]
    }
    
    print("Example 1: Simple users")
    print("=" * 50)
    print("JSON:")
    json_str = json.dumps(data1, indent=2)
    print(json_str)
    print(f"\nTokens: {count_tokens(json_str)}")
    
    print("\nTOON:")
    toon_str = json_to_toon(json.dumps(data1))
    print(toon_str)
    print(f"\nTokens: {count_tokens(toon_str)}")
    
    print("\n" + "=" * 50)
    
    # Example 2: Hikes data
    data2 = {
        "context": {
            "task": "Our favorite hikes together",
            "location": "Boulder",
            "season": "spring_2025"
        },
        "friends": ["ana", "luis", "sam"],
        "hikes": [
            {
                "id": 1,
                "name": "Blue Lake Trail",
                "distanceKm": 7.5,
                "elevationGain": 320,
                "companion": "ana",
                "wasSunny": True
            },
            {
                "id": 2,
                "name": "Ridge Overlook",
                "distanceKm": 9.2,
                "elevationGain": 540,
                "companion": "luis",
                "wasSunny": False
            }
        ]
    }
    
    print("\nExample 2: Hikes data")
    print("=" * 50)
    print("TOON:")
    toon_str2 = json_to_toon(json.dumps(data2))
    print(toon_str2)
