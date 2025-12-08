"""
Azure Key Vault client for secure credential management.

Implements WO-15: Secure Connection Strings and Keys with Azure Key Vault
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Conditional import for Azure Key Vault SDK
try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    KEY_VAULT_AVAILABLE = True
except ImportError:
    KEY_VAULT_AVAILABLE = False
    SecretClient = None
    DefaultAzureCredential = None
    ManagedIdentityCredential = None


class KeyVaultClient:
    """
    Client for retrieving secrets from Azure Key Vault.
    
    Supports:
    - Managed Identity authentication (for Azure Functions)
    - Default Azure Credential (for local development)
    - Fallback to environment variables
    """
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Initialize Key Vault client.
        
        Args:
            vault_url: Azure Key Vault URL (optional, can be set via env var)
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self._client: Optional[SecretClient] = None
        self._cache: dict = {}
        
        if not KEY_VAULT_AVAILABLE:
            logger.warning(
                "Azure Key Vault SDK not available. "
                "Will use environment variables as fallback."
            )
            return
        
        if not self.vault_url:
            logger.warning(
                "Azure Key Vault URL not configured. "
                "Will use environment variables as fallback."
            )
            return
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Key Vault secret client."""
        if not KEY_VAULT_AVAILABLE or not self.vault_url:
            return
        
        try:
            # Try Managed Identity first (for Azure Functions)
            # Then fall back to DefaultAzureCredential (for local dev)
            try:
                credential = ManagedIdentityCredential()
                logger.debug("Using Managed Identity credential")
            except Exception:
                credential = DefaultAzureCredential()
                logger.debug("Using Default Azure Credential")
            
            self._client = SecretClient(
                vault_url=self.vault_url,
                credential=credential
            )
            logger.info(f"Key Vault client initialized: {self.vault_url}")
            
        except Exception as e:
            logger.warning(
                f"Failed to initialize Key Vault client: {e}. "
                "Will use environment variables as fallback.",
                exc_info=True
            )
            self._client = None
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Retrieve a secret from Key Vault.
        
        Args:
            secret_name: Name of the secret in Key Vault
            use_cache: Whether to use cached value (default: True)
            
        Returns:
            Secret value or None if not found
        """
        # Check cache first
        if use_cache and secret_name in self._cache:
            return self._cache[secret_name]
        
        # Try Key Vault if available
        if self._client:
            try:
                secret = self._client.get_secret(secret_name)
                value = secret.value
                
                # Cache the value
                self._cache[secret_name] = value
                
                logger.debug(f"Retrieved secret from Key Vault: {secret_name}")
                return value
                
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve secret from Key Vault '{secret_name}': {e}. "
                    "Falling back to environment variable.",
                    exc_info=True
                )
        
        # Fallback to environment variable
        env_var_name = secret_name.upper().replace("-", "_")
        value = os.getenv(env_var_name) or os.getenv(secret_name)
        
        if value:
            logger.debug(f"Retrieved secret from environment variable: {env_var_name}")
            # Cache the value
            self._cache[secret_name] = value
            return value
        
        logger.warning(f"Secret not found in Key Vault or environment: {secret_name}")
        return None
    
    def get_connection_string(self, connection_string_name: str) -> Optional[str]:
        """
        Retrieve a connection string from Key Vault.
        
        This is a convenience method that calls get_secret().
        
        Args:
            connection_string_name: Name of the connection string secret
            
        Returns:
            Connection string or None if not found
        """
        return self.get_secret(connection_string_name)
    
    def clear_cache(self):
        """Clear the secret cache."""
        self._cache.clear()
        logger.debug("Key Vault cache cleared")


# Global Key Vault client instance
_key_vault_client: Optional[KeyVaultClient] = None


def get_key_vault_client() -> KeyVaultClient:
    """Get or initialize the global Key Vault client."""
    global _key_vault_client
    
    if _key_vault_client is None:
        _key_vault_client = KeyVaultClient()
    
    return _key_vault_client


def get_connection_string_from_key_vault(secret_name: str) -> Optional[str]:
    """
    Convenience function to get a connection string from Key Vault.
    
    Args:
        secret_name: Name of the secret in Key Vault
        
    Returns:
        Connection string or None if not found
    """
    client = get_key_vault_client()
    return client.get_connection_string(secret_name)

