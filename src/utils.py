"""Utility functions for cursor encoding/decoding and seed management."""
import base64
import os

# Set deterministic hash seed
os.environ['PYTHONHASHSEED'] = '0'


def encode_cursor(product_id: str, offset: int, seed: int) -> str:
    """Encode cursor as URL-safe base64 string.
    
    Args:
        product_id: Product ID
        offset: Current offset
        seed: Random seed for tie-breaking
        
    Returns:
        Base64-encoded cursor string
    """
    cursor_str = f"{product_id}|{offset}|{seed}"
    return base64.urlsafe_b64encode(cursor_str.encode()).decode()


def decode_cursor(cursor: str) -> tuple[str, int, int]:
    """Decode cursor from URL-safe base64 string.
    
    Args:
        cursor: Base64-encoded cursor string
        
    Returns:
        Tuple of (product_id, offset, seed)
    """
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        parts = decoded.split('|')
        if len(parts) != 3:
            raise ValueError("Invalid cursor format")
        return parts[0], int(parts[1]), int(parts[2])
    except Exception:
        raise ValueError("Invalid cursor format")

