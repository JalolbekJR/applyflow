import re
import unicodedata
from datetime import date
from urllib.parse import urlsplit

from rest_framework import serializers

from .models import CandidateFields

PHONE_PATTERN = re.compile(r"^[+()\d \-]{7,30}$")
MONTH_PATTERN = re.compile(r"^(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])$")
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


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail("invalid")
        return super().to_internal_value(data)


class StrictStringField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class StrictMonthField(serializers.Field):
    default_error_messages = {
        "invalid": "Enter a month in YYYY-MM format.",
    }

    def to_internal_value(self, data):
        if not isinstance(data, str) or not data.isascii():
            self.fail("invalid")
        match = MONTH_PATTERN.fullmatch(data)
        if match is None:
            self.fail("invalid")
        return date(int(match.group("year")), int(match.group("month")), 1)

    def to_representation(self, value):
        if value is None:
            return None
        return value.strftime("%Y-%m")


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
            raise serializers.ValidationError("Enter a secure link starting with https://.")
        value = value.strip()
        if value:
            parts = urlsplit(value)
            try:
                _ = parts.port
            except ValueError:
                raise serializers.ValidationError(
                    "Enter a secure link starting with https://."
                ) from None
            if parts.scheme.lower() != "https":
                raise serializers.ValidationError("Enter a secure link starting with https://.")
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


class DraftExperienceEntrySerializer(DraftSectionSerializer):
    organization = StrictStringField(required=False, max_length=160, trim_whitespace=False)
    role_title = StrictStringField(required=False, max_length=160, trim_whitespace=False)
    start_month = StrictMonthField(required=False)
    end_month = StrictMonthField(required=False, allow_null=True)
    is_current = StrictBooleanField(required=False)
    summary = StrictStringField(
        required=False,
        allow_blank=True,
        max_length=600,
        trim_whitespace=False,
    )
    position = StrictIntegerField(required=False, min_value=0, max_value=4)

    def validate_organization(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter an organization without control characters.")
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_role_title(self, value):
        if has_disallowed_control(value):
            raise serializers.ValidationError("Enter a role title without control characters.")
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_summary(self, value):
        if has_disallowed_control(value, allow_line_breaks=True):
            raise serializers.ValidationError("Use plain text with normal line breaks.")
        return value

    def validate(self, attrs):
        instance = self.instance

        def merged_value(name):
            if name in attrs:
                return attrs[name]
            if instance is not None:
                return getattr(instance, name)
            return None

        errors = {}
        for name in ("organization", "role_title", "start_month", "is_current", "position"):
            if merged_value(name) is None:
                errors[name] = ["This field is required."]

        start_month = merged_value("start_month")
        end_month = merged_value("end_month")
        is_current = merged_value("is_current")
        if is_current is True and end_month is not None:
            errors["end_month"] = ["Clear the end month for a current role."]
        if is_current is False and end_month is None:
            errors["end_month"] = ["Add an end month for a completed role."]
        if start_month is not None and end_month is not None and end_month < start_month:
            errors["end_month"] = [
                "Choose an end month that is the same as or after the start month."
            ]

        draft = self.context.get("draft")
        position = merged_value("position")
        if draft is not None and position is not None:
            siblings = draft.experience_entries.all()
            if instance is not None:
                siblings = siblings.exclude(pk=instance.pk)
            if siblings.filter(position=position).exists():
                errors["position"] = ["Choose a unique position from 0 to 4."]
            if instance is None and draft.experience_entries.count() >= 5:
                errors["non_field_errors"] = ["You can add up to five employment entries."]

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


def public_experience_entry(entry):
    return {
        "id": entry.pk,
        "organization": entry.organization,
        "role_title": entry.role_title,
        "start_month": StrictMonthField().to_representation(entry.start_month),
        "end_month": StrictMonthField().to_representation(entry.end_month),
        "is_current": entry.is_current,
        "summary": entry.summary,
        "position": entry.position,
    }


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
            "experience_entries": [
                public_experience_entry(entry) for entry in draft.experience_entries.all()
            ],
            "document": document_payload,
            "last_activity_at": draft.last_activity_at,
            "expires_at": draft.expires_at,
        }
    }
