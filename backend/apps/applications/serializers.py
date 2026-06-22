def public_draft(draft):
    document = draft.documents.filter(deleted_at__isnull=True).first()
    document_payload = None
    if document is not None:
        document_payload = {
            "original_name_display": document.original_name_display,
            "detected_content_type": document.detected_content_type,
            "size": document.size,
            "uploaded_at": document.uploaded_at,
        }

    return {
        "draft": {
            "id": draft.pk,
            "status": draft.status,
            "version": draft.version,
            "vacancy": {"slug": draft.vacancy.slug, "title": draft.vacancy.title},
            "candidate": {
                "full_name": draft.full_name,
                "email": draft.email,
                "phone": draft.phone,
                "portfolio_url": draft.portfolio_url,
                "preferred_contact_method": draft.preferred_contact_method,
            },
            "experience": {
                "experience_level": draft.experience_level,
                "skills": draft.skills,
                "optional_message": draft.optional_message,
                "consent_acknowledged": draft.consent_acknowledged,
                "consent_version": draft.consent_version,
            },
            "experience_entries": [],
            "document": document_payload,
            "last_activity_at": draft.last_activity_at,
            "expires_at": draft.expires_at,
        }
    }
