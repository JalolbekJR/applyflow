import re
import unicodedata
from urllib.parse import urlsplit

from rest_framework import serializers

from .models import CandidateFields

PHONE_PATTERN = re.compile(r"^[+()\d \-]{7,30}$")
MAX_SKILL_LENGTH = 80


def has_disallowed_control(value: str, *, allow_line_breaks=False) -> bool:
    allowed = {"\r", "\n"} if allow_line_breaks else set()
    return any(
        character not in allowed and unicodedata.category(character).startswith("C")
        for character in value
    )


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if type(data) is not bool:
            self.fail("invalid")
        return data


class DraftSectionSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                {"non_field_errors": ["Send the fields to update as a JSON object."]}
            )
        if not data:
            raise serializers.ValidationError(
                {"non_field_errors": ["Add at least one field to update."]}
            )
        unknown = sorted(set(data) - set(self.fields))
        if unknown:
            raise serializers.ValidationError(
                {field: ["This field cannot be updated here."] for field in unknown}
            )
        return super().to_internal_value(data)


class CandidatePatchSerializer(DraftSectionSerializer):
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    email = serializers.EmailField(required=False, allow_blank=True, max_length=254)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=32)
    portfolio_url = serializers.URLField(
        required=False,
        allow_blank=True,
        max_length=500,
    )
    preferred_contact_method = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=CandidateFields.ContactMethod.choices,
    )

    def validate_full_name(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter a name without control characters.")
        return value.strip()

    def validate_email(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter a valid email address.")
        return value.strip()

    def validate_phone(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter a phone number using common phone symbols.")
        value = value.strip()
        if value and not PHONE_PATTERN.fullmatch(value):
            raise serializers.ValidationError("Enter a phone number using common phone symbols.")
        return value

    def validate_portfolio_url(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter a valid HTTP or HTTPS link.")
        value = value.strip()
        if value and urlsplit(value).scheme.lower() not in {"http", "https"}:
            raise serializers.ValidationError("Enter a valid HTTP or HTTPS link.")
        return value

    def validate(self, attrs):
        phone = attrs.get("phone", self.instance.phone)
        preference = attrs.get(
            "preferred_contact_method",
            self.instance.preferred_contact_method,
        )
        if preference == CandidateFields.ContactMethod.PHONE and not phone:
            raise serializers.ValidationError(
                {"phone": ["Add a phone number before choosing phone contact."]}
            )
        return attrs


class ExperiencePatchSerializer(DraftSectionSerializer):
    experience_level = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=CandidateFields.ExperienceLevel.choices,
    )
    skills = serializers.ListField(required=False, allow_empty=True)
    optional_message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1200,
        trim_whitespace=False,
    )
    consent_acknowledged = StrictBooleanField(required=False)
    consent_version = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=64,
        trim_whitespace=False,
    )

    def validate_skills(self, value):
        if len(value) > 12:
            raise serializers.ValidationError("Add no more than 12 skills.")
        normalized = []
        seen = set()
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Use text for each skill.")
            if has_disallowed_control(item):
                raise serializers.ValidationError("Use skill names without control characters.")
            item = item.strip()
            if not item:
                raise serializers.ValidationError("Remove blank skills.")
            if len(item) > MAX_SKILL_LENGTH:
                raise serializers.ValidationError(
                    f"Keep each skill to {MAX_SKILL_LENGTH} characters or fewer."
                )
            key = item.casefold()
            if key not in seen:
                normalized.append(item)
                seen.add(key)
        return normalized

    def validate_optional_message(self, value):
        if has_disallowed_control(value, allow_line_breaks=True):
            raise serializers.ValidationError(
                "Use plain text with normal line breaks in the short message."
            )
        return value

    def validate_consent_version(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter a valid consent version.")
        return value


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
