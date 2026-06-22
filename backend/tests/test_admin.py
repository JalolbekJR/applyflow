from django.contrib import admin


def test_domain_models_are_registered_without_sensitive_fields():
    expected = {
        "vacancy",
        "applicationdraft",
        "application",
        "applicationdocument",
    }
    registered = {model._meta.model_name for model in admin.site._registry}
    assert expected <= registered

    required_exclusions = {
        "applicationdraft": "secret_hash",
        "application": "status_lookup_secret_hash",
        "applicationdocument": "storage_key",
    }
    for model, model_admin in admin.site._registry.items():
        if model._meta.model_name in required_exclusions:
            assert required_exclusions[model._meta.model_name] in model_admin.exclude
