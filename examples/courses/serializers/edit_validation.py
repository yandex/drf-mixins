from typing import Sequence

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from courses.models import Course, CourseBlock, CourseModule
from courses.serializers.module_content_lab import is_migrated_course
from courses.validation import (
    COURSE_SETTINGS_VALIDATORS,
    COURSE_VALIDATORS,
    LANGUAGE_VALIDATORS,
)
from courses.validation.errors import MODULE_VALIDATION_ERROR
from courses.validation.prefetch import (
    language_validation_result,
    prefetch_course_for_validation,
)
from courses.validation.runner import course_validate
from lms.quizzes.models import Quiz

MODULE_EDIT_INVALID_MESSAGE = _("Check that the module fields are filled in correctly")
BLOCK_EDIT_INVALID_MESSAGE = _("Check that the block fields are filled in correctly")
BLOCK_MODULES_EDIT_INVALID_MESSAGE = _(
    "Check that the block module fields are filled in correctly"
)
COURSE_PUBLISH_INVALID_MESSAGE = _(
    "Cannot publish the course: not all required fields are filled in"
)
LANGUAGE_PUBLISH_INVALID_MESSAGE = _(
    "Cannot publish the language: not all required fields are filled in"
)
COURSE_SETTINGS_EDIT_INVALID_MESSAGE = _(
    "Cannot save settings: not all required fields are filled in"
)


def published_multilanguage_course(course) -> bool:
    """Return whether the course is multilingual and published."""
    return is_migrated_course(course) and course.is_active


def _module_block_published(module) -> bool:
    """Validate a module only when its block is published or it is orphaned."""
    if module.block_id is None:
        return True
    return (
        CourseBlock.objects.filter(pk=module.block_id)
        .values_list("is_active", flat=True)
        .first()
        is True
    )


def guard_active_module_edit(module: CourseModule) -> None:
    result = language_validation_result(module.course_id, LANGUAGE_VALIDATORS)
    if result is None:
        return
    if any(
        language.is_active and not result.is_module_valid(module.id, language.language)
        for language in result.languages
    ):
        raise serializers.ValidationError(MODULE_EDIT_INVALID_MESSAGE)


def guard_active_block_edit(block: CourseBlock) -> None:
    result = language_validation_result(block.course_id, LANGUAGE_VALIDATORS)
    if result is None:
        return
    invalid_languages = {
        language.language
        for language in result.languages
        if language.is_active and not result.is_block_valid(block.id, language.language)
    }
    if not invalid_languages:
        return
    # If modules make the block invalid, rather than only a field on the block
    # itself, return a separate message about the block modules.
    block_module_ids = set(
        CourseModule.objects.filter(block_id=block.id).values_list("id", flat=True)
    )
    modules_triggered = any(
        error.code == MODULE_VALIDATION_ERROR
        and error.entity_id in block_module_ids
        and error.language in invalid_languages
        for error in result.errors
    )
    message = (
        BLOCK_MODULES_EDIT_INVALID_MESSAGE
        if modules_triggered
        else BLOCK_EDIT_INVALID_MESSAGE
    )
    raise serializers.ValidationError(message)


class ModuleEditValidationSerializerMixin:
    def _should_run_module_edit_guard(self, instance) -> bool:
        return (
            instance.is_active
            and published_multilanguage_course(instance.course)
            and _module_block_published(instance)
        )

    def create(self, validated_data):
        instance = super().create(validated_data)
        if self._should_run_module_edit_guard(instance):
            guard_active_module_edit(instance)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if self._should_run_module_edit_guard(instance):
            guard_active_module_edit(instance)
        return instance


class QuizEditValidationSerializerMixin(ModuleEditValidationSerializerMixin):
    def _should_run_module_edit_guard(self, instance) -> bool:
        return (
            instance.status == Quiz.Status.PUBLISHED
            and super()._should_run_module_edit_guard(instance)
        )


def guard_course_publish(course_id: int) -> None:
    course = (
        prefetch_course_for_validation(Course.objects.all())
        .filter(pk=course_id)
        .first()
    )
    if course is None or not is_migrated_course(course):
        return
    result = course_validate(course, validators=COURSE_VALIDATORS)
    if not result.is_valid:
        raise serializers.ValidationError(COURSE_PUBLISH_INVALID_MESSAGE)


def guard_course_settings_edit(course_id: int) -> None:
    course = (
        prefetch_course_for_validation(Course.objects.all())
        .filter(pk=course_id)
        .first()
    )
    if course is None or not is_migrated_course(course):
        return
    result = course_validate(course, validators=COURSE_SETTINGS_VALIDATORS)
    active_languages = {
        language.language for language in result.languages if language.is_active
    }
    if any(
        error.language is None or error.language in active_languages
        for error in result.errors
    ):
        raise serializers.ValidationError(COURSE_SETTINGS_EDIT_INVALID_MESSAGE)


def guard_language_publish(course_id: int, activated_languages: Sequence[str]) -> None:
    if not activated_languages:
        return
    result = language_validation_result(course_id, LANGUAGE_VALIDATORS)
    if result is None:
        return
    for lang_code in activated_languages:
        if not result.is_language_valid(lang_code):
            raise serializers.ValidationError(LANGUAGE_PUBLISH_INVALID_MESSAGE)


def detect_activated_languages(
    course: Course,
    supported_languages: list[dict] | None,
) -> list[str]:
    if not supported_languages:
        return []

    old_states: dict[str, bool] = dict(
        course.content_languages.values_list("language", "is_active")
    )

    activated: list[str] = []
    for item in supported_languages:
        code = item["language_code"]
        new_active = item.get("is_active", True)
        was_active = old_states.get(code)
        if new_active and not was_active:
            activated.append(code)

    return activated
