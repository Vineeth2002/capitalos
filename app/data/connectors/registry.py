_REGISTRY = {}


def register_connector(provider_name, connector_class):
    # Registers a connector class under its provider_name. The ingestion
    # service and any future caller look up connectors ONLY through this
    # registry - never by importing a specific connector class directly.
    # This is what makes adding Provider N a matter of calling
    # register_connector() once, not modifying any existing file that
    # already knows about Providers A through N-1.
    _REGISTRY[provider_name] = connector_class


def get_connector_class(provider_name):
    if provider_name not in _REGISTRY:
        raise KeyError("No connector registered for provider: " + provider_name)
    return _REGISTRY[provider_name]


def list_registered_providers():
    return list(_REGISTRY.keys())


def clear_registry():
    # Test-only helper, so tests registering temporary providers (like a
    # throwaway "Provider C") don't leak into other tests.
    _REGISTRY.clear()