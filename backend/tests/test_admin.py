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
        "applicationdraft": {"secret_hash", "creation_key_digest"},
        "application": "status_lookup_secret_hash",
        "applicationdocument": "storage_key",
    }
    for model, model_admin in admin.site._registry.items():
        if model._meta.model_name in required_exclusions:
            required = required_exclusions[model._meta.model_name]
            if isinstance(required, str):
                required = {required}
            assert required <= set(model_admin.exclude)

    draft_admin = next(
        model_admin
        for model, model_admin in admin.site._registry.items()
        if model._meta.model_name == "applicationdraft"
    )
    assert {"version", "last_activity_at", "credential_revoked_at"} <= set(
        draft_admin.readonly_fields
    )
    assert {"version", "last_activity_at"} <= set(draft_admin.list_display)
