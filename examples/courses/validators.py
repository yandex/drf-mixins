from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_course_slug(value) -> None:
    """
    Validate the course slug in a serializer.
    """
    if value in settings.COURSE_RESERVED_SLUGS:
        raise ValidationError(
            _("'{value}' cannot be used as a course code").format(value=value),
            code="invalid",
        )
