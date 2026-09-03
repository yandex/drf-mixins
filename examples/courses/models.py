import logging
from datetime import datetime
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Min, Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_json_field_schema_validator.validators import JSONFieldSchemaValidator
from model_utils import FieldTracker
from model_utils.models import TimeStampedModel
from ordered_model.models import OrderedModel
from simple_history.models import HistoricalRecords

from lms.bookmarks.models import Bookmark, BookmarkAuthor
from lms.core.models.mixins import ActiveModelMixin, HrdbIdModelMixin
from lms.courseteams.models import CourseTeam as CourseTeamNew
from lms.moduletypes.models import Module as BaseModule
from lms.preferences.models import ColorTheme
from lms.tags.models import Tag

from .managers import CourseGroupManager
from .mixins import AvailabilityMixin
from .querysets import (
    CourseBlockQuerySet,
    CourseCategoryQuerySet,
    CourseGroupQuerySet,
    CourseModuleQuerySet,
    CourseQuerySet,
    CourseStudentQuerySet,
    StudyModeQuerySet,
)
from .utils import count_course_student_price
from .validators import validate_course_slug

logger = logging.getLogger(__name__)

User = get_user_model()


class StudyMode(ActiveModelMixin, OrderedModel, TimeStampedModel):
    slug = models.SlugField(_("code"), max_length=255, blank=True, unique=True)
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    objects = StudyModeQuerySet.as_manager()

    class Meta(OrderedModel.Meta):
        verbose_name = _("study mode")
        verbose_name_plural = _("study modes")

    def __str__(self):
        return f"{self.name} [{self.slug}]" if self.slug else self.name


class CourseCategory(TimeStampedModel):
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent category"),
        related_name="children",
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.PROTECT,
    )

    slug = models.SlugField(_("code"), max_length=255, unique=True)
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    color_theme = models.ForeignKey(
        ColorTheme,
        verbose_name=_("color scheme"),
        related_name="categories",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    is_active = models.BooleanField(_("active"), default=True)
    created_by = models.ForeignKey(
        User,
        verbose_name=_("created"),
        related_name="created_course_categories",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = CourseCategoryQuerySet.as_manager()

    class Meta:
        ordering = ("name",)
        verbose_name = _("course category")
        verbose_name_plural = _("course categories")

    def __str__(self):
        return self.name

    @property
    def with_courses(self) -> bool:
        return self.courses.exists()


class CourseSettings(models.Model):
    class PaymentMethodChoices(models.TextChoices):
        FREE = "free", _("Free")
        CORPORATE = "corporate", _("Company-funded")
        PERSONAL = "personal", _("Payroll deduction")

    PAYMENT_METHOD_CHOICES_TRANSLATIONS = {
        "free": {
            "ru": "Free",
            "en": "Free",
        },
        "corporate": {
            "ru": "Company-funded",
            "en": "Corporate",
        },
        "personal": {
            "ru": "Payroll deduction",
            "en": "Personal",
        },
    }

    begin_date = models.DateTimeField(
        _("study start"), null=True, blank=True, db_index=True
    )
    end_date = models.DateTimeField(
        _("study end"), null=True, blank=True, db_index=True
    )

    enroll_begin = models.DateTimeField(
        _("enrollment start"), null=True, blank=True, db_index=True
    )
    enroll_end = models.DateTimeField(
        _("enrollment end"), null=True, blank=True, db_index=True
    )

    price = models.DecimalField(
        _("catalog price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Full price requested by the provider"),
    )

    payment_method = models.CharField(
        _("payment method"),
        max_length=20,
        choices=PaymentMethodChoices.choices,
        default=PaymentMethodChoices.FREE,
    )

    paid_percent = models.IntegerField(
        _("deduction percentage"),
        default=0,
        help_text=_("Relevant only when the employee pays"),
    )
    payment_terms = models.TextField(
        _("payment terms"),
        blank=True,
        help_text=_("Description of payment terms, deductions, and company cost"),
    )
    estimated_time = models.PositiveIntegerField(
        _("completion time"),
        null=True,
        blank=True,
        help_text=_("minutes"),
    )

    @property
    def student_price(self) -> int | None:
        if self.price is not None:
            return count_course_student_price(self.price, self.paid_percent)

    @property
    def is_enroll_open(self) -> bool:
        raise NotImplementedError()

    @property
    def is_full(self) -> bool:
        raise NotImplementedError()

    @property
    def has_open_seats(self) -> bool:
        return not self.is_full

    class Meta:
        abstract = True

    def check_enroll_open(self, now=None) -> bool:
        """
        Check whether enrollment is open at the given time.

        :param now:
        :return:
        """
        return self.enroll_open_for_dates(self.enroll_begin, self.enroll_end, now=now)

    def enroll_open_for_dates(self, enroll_begin, enroll_end, now=None) -> bool:
        if now is None:
            now = timezone.now().replace(second=0, microsecond=0)

        if enroll_begin is None and enroll_end is None:
            return True
        if enroll_begin is None:
            return now <= enroll_end
        if enroll_end is None:
            return enroll_begin <= now

        return enroll_begin <= now <= enroll_end

    def clean_paid_precent(self):
        if self.payment_method != self.PaymentMethodChoices.PERSONAL:
            self.paid_percent = 0
        if self.payment_method == self.PaymentMethodChoices.FREE:
            self.price = None

    def save(self, *args, **kwargs):
        self.clean_paid_precent()
        super().save(*args, **kwargs)


class Course(AvailabilityMixin, CourseSettings, TimeStampedModel, HrdbIdModelMixin):
    class StructureChoices(models.TextChoices):
        NO_MODULES = "no_modules", _("No modules")
        SINGLE = "single_module", _("Single module")
        MULTI = "multi_modules", _("Multiple modules")

    class FormatChoices(models.TextChoices):
        SELF_STUDY = "self_study", _("Self-paced")
        WITH_TEACHER = "with_teacher", _("Instructor-led")

    class TypeChoices(models.TextChoices):
        COURSE = "course", _("Course")
        TRACK = "track", _("Program")
        OTHER = "other", _("Other")

    class StartModeTypeChoices(models.TextChoices):
        ANY_TIME = "any_time", _("Any time")
        AFTER_GROUP_FILLED = "after_group_filled", _("After the cohort is filled")
        FIXED_DATES = "fixed_dates", _("Fixed date")

    class DescriptionVersionChoices(models.IntegerChoices):
        OLD = 1
        NEW = 2

    begin_date_field = "calc_begin_date"
    end_date_field = "calc_end_date"
    enroll_begin_field = "calc_enroll_begin"
    enroll_end_field = "calc_enroll_end"

    hrdb_id = models.IntegerField(
        _("HRDB ID"),
        blank=True,
        null=True,
        unique=True,
        help_text=_("Identifier in HRDB"),
    )

    categories = models.ManyToManyField(
        CourseCategory,
        verbose_name=_("categories"),
        related_name="courses",
        blank=True,
    )
    study_mode = models.ForeignKey(
        StudyMode,
        verbose_name=_("study mode"),
        related_name="courses",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name=_("author"),
        related_name="courses",
        on_delete=models.PROTECT,
    )
    teams = models.ManyToManyField(
        CourseTeamNew,
        verbose_name=_("course teams"),
        related_name="courses",
        blank=True,
    )
    enable_groups = models.BooleanField(
        verbose_name=_("Has student groups"),
        default=False,
        editable=False,
    )
    enable_followers = models.BooleanField(
        verbose_name=_("allow course subscriptions"),
        default=False,
        help_text=_("all course subscriptions are allowed"),
    )

    slug = models.SlugField(
        _("code"),
        max_length=255,
        unique=True,
        validators=[validate_course_slug],
    )
    name = models.CharField(_("name"), max_length=255, db_index=True)
    shortname = models.CharField(_("short name"), max_length=255, blank=True)
    summary = models.CharField(_("summary"), max_length=2048, blank=True)
    description = models.TextField(_("description"), blank=True)
    target_audience_description = models.TextField(
        _("target audience"), default="", blank=True
    )
    image_url = models.URLField(_("cover"), max_length=500, blank=True)

    is_active = models.BooleanField(_("active"), default=False)
    is_archive = models.BooleanField(_("archived"), default=False)

    calc_begin_date = models.DateTimeField(
        _("actual study start"), null=True, blank=True, editable=False
    )
    calc_end_date = models.DateTimeField(
        _("actual study end"), null=True, blank=True, editable=False
    )

    calc_enroll_begin = models.DateTimeField(
        _("actual enrollment start"), null=True, blank=True, editable=False
    )
    calc_enroll_end = models.DateTimeField(
        _("actual enrollment end"), null=True, blank=True, editable=False
    )

    structure = models.CharField(
        _("course structure"),
        max_length=20,
        choices=StructureChoices.choices,
        default=StructureChoices.NO_MODULES,
    )

    format = models.CharField(  # noqa: A003
        _("study format"),
        max_length=20,
        choices=FormatChoices.choices,
        blank=True,
    )

    retries_allowed = models.BooleanField(
        _("course retake"),
        default=True,
        help_text=_(
            "After completing the course, the user can enroll again and retake it"
        ),
    )

    completion_threshold = models.PositiveSmallIntegerField(
        _("completion threshold"),
        default=100,
        validators=[MaxValueValidator(100)],
        help_text=_("Completion percentage required to finish the course"),
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name=_("tags"),
        related_name="courses",
        blank=True,
    )

    objects = CourseQuerySet.as_manager()

    tracker = FieldTracker(
        fields=[
            "enable_followers",
            "enroll_begin",
            "enroll_end",
            "is_active",
            "is_archive",
            "name",
        ]
    )

    course_type = models.CharField(
        _("type"),
        max_length=20,
        choices=TypeChoices.choices,
        default=TypeChoices.COURSE,
    )
    description_version = models.IntegerField(
        choices=DescriptionVersionChoices.choices, default=DescriptionVersionChoices.OLD
    )

    start_mode = models.CharField(
        _("start mode"),
        max_length=30,
        choices=StartModeTypeChoices.choices,
        default=StartModeTypeChoices.ANY_TIME,
        blank=True,
        null=True,
    )

    is_audit = models.BooleanField(_("auditable"), default=False)

    rating = models.FloatField(_("rating"), null=True, blank=True)
    number_ratings = models.PositiveIntegerField(
        _("number of ratings"), blank=True, default=0
    )

    migrated_to_avatars = models.BooleanField(_("migrated to Avatars"), default=True)

    def get_maximum_capacity(self):
        occ = getattr(self, "occupancy", None)
        return occ.maximum if occ else None

    def get_current_capacity(self):
        occ = getattr(self, "occupancy", None)
        return occ.current if occ else None

    @property
    def is_full(self) -> bool:
        """
        Return whether the course has available places.

        For grouped courses, check places in groups that are open for enrollment.
        """
        # Places are unlimited for courses without groups.
        if not self.enable_groups:
            return False

        for group in self.opened_groups:  # type: CourseGroup
            if (
                group.max_participants == 0
                or group.num_participants < group.max_participants
            ):
                return False

        return True

    @property
    def frontend_url(self) -> str:
        return f"{settings.FRONTEND_ROOT}/{self.course_type}s/{self.slug}"

    @property
    def frontend_lab_url(self) -> str:
        return f"{settings.FRONTEND_LAB_ROOT}/{self.course_type}s/{self.slug}"

    @property
    def admin_url(self) -> str:
        return f"{settings.ADMIN_ROOT}/courses/course/{self.id}"

    @property
    def opened_groups(self, now=None):
        """
        Return course groups that are open for enrollment.

        Check `_opened_groups` first so callers can prefetch groups.
        :param now:
        :return:
        """
        return getattr(self, "_opened_groups", self.groups.opened(now))

    def check_enroll_open(self, now=None) -> bool:
        """
        Course-level enroll_begin/enroll_end dates are ignored; availability is
        determined only by is_active, which is checked by the caller. For courses
        with groups or scheduled classes, dates are checked by
        CourseGroup.check_enroll_open().
        """
        return True

    @property
    def is_enroll_open(self) -> bool:
        """
        Return whether course enrollment is open.

        For grouped courses, at least one group must be open for enrollment.
        :return:
        """
        if not self.is_active:
            return False

        now = timezone.now().replace(second=0, microsecond=0)

        # Courses with groups or scheduled classes can only be taken through a
        # group. Enrollment is open when at least one group is open; when no
        # groups exist yet, there is nowhere to enroll.
        if self.enable_groups:
            return self.opened_groups.exists()
        else:
            return self.check_enroll_open(now)

    @cached_property
    def available_for_enroll(self) -> bool:
        return super().available_for_enroll

    @cached_property
    def enroll_will_begin(self) -> Optional[datetime]:
        """
        :return: whether upcoming enrollments exist
        """
        if not self.is_active:
            return None

        now = timezone.now().replace(second=0, microsecond=0)

        if self.enable_groups:
            aggr = self.groups.available().aggregate(
                nearest_enroll_begin=Min(
                    "enroll_begin", filter=Q(enroll_begin__gte=now)
                ),
            )
            enroll_begin = aggr.get("nearest_enroll_begin")
        else:
            enroll_begin = None

        if enroll_begin is not None and enroll_begin > now:
            return enroll_begin

        return None

    class Meta:
        ordering = ("name",)
        verbose_name = _("course")
        verbose_name_plural = _("courses")
        permissions = (
            ("import_course", _("Can import courses")),
            ("export_course", _("Can export courses")),
            ("enroll_to_course", _("Can enroll to courses")),
        )

    def clean(self):
        if self.is_active:
            if self.structure == self.StructureChoices.NO_MODULES:
                if not self.estimated_time:
                    raise ValidationError(
                        _("The course duration must be specified"),
                        code="invalid",
                    )
            else:
                if not self.modules.filter(is_active=True).exists():
                    raise ValidationError(
                        _("The course must contain modules"),
                        code="invalid",
                    )
                if (
                    self.modules.filter(is_active=True)
                    .exclude(module_type__model="classroom")
                    .filter(Q(estimated_time=0) | Q(estimated_time__isnull=True))
                    .exists()
                ):
                    raise ValidationError(
                        _("Durations must be specified for all modules"),
                        code="invalid",
                    )

    def save(self, *args, **kwargs):
        if self.course_type == self.TypeChoices.TRACK:
            self.structure = self.StructureChoices.MULTI
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        s = f"{self.name} [id={self.pk}]"
        if self.slug:
            s += f"[{self.slug}]"
        return s

    def get_group_or_course_field(self, field_name):
        return getattr(self, field_name, None)


def get_default_program():
    return {"group_blocks": True, "blocks": []}


class CourseProgram(TimeStampedModel):
    PROGRAM_SCHEMA = {
        "definitions": {
            "module_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 255,
                    },
                    "hours": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "minutes": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 59,
                    },
                },
                "required": ["title"],
                "additionalProperties": False,
            },
        },
        "type": "object",
        "properties": {
            "group_blocks": {
                "type": "boolean",
            },
            "blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "maxLength": 255,
                        },
                        "modules": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/module_schema"},
                        },
                    },
                    "required": ["title", "modules"],
                    "additionalProperties": False,
                },
            },
            "modules": {
                "type": "array",
                "items": {"$ref": "#/definitions/module_schema"},
            },
        },
        "oneOf": [
            {"required": ["group_blocks", "blocks"]},
            {"required": ["group_blocks", "modules"]},
        ],
        "additionalProperties": False,
    }

    course = models.OneToOneField(
        Course,
        primary_key=True,
        verbose_name=_("course"),
        related_name="program",
        on_delete=models.CASCADE,
    )
    program = models.JSONField(
        validators=[JSONFieldSchemaValidator(schema=PROGRAM_SCHEMA)],
        default=get_default_program,
    )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Course program")
        verbose_name_plural = _("Course programs")

    def __str__(self):
        if hasattr(self, "course"):
            return f"Program for course {self.course}"
        return "Program"


class CourseTutor(TimeStampedModel):
    course = models.OneToOneField(
        Course,
        verbose_name=_("course"),
        related_name="tutor",
        primary_key=True,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("curator"),
        related_name="course_tutor",
        on_delete=models.CASCADE,
    )
    hide = models.BooleanField(
        _("hide"),
        default=False,
        help_text=_("do not show on the course card"),
    )

    class Meta:
        verbose_name = _("Course curator")
        verbose_name_plural = _("Course curators")


class CourseTeacher(TimeStampedModel):
    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="teachers",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("instructor"),
        related_name="course_teachers",
        on_delete=models.CASCADE,
    )
    role = models.CharField(
        _("role"),
        max_length=255,
        blank=True,
    )

    class Meta:
        verbose_name = _("Instructor, presenter, or other")
        verbose_name_plural = _("Instructors, presenters, and others")


class CourseOccupancy(TimeStampedModel):
    course = models.OneToOneField(
        Course,
        verbose_name=_("course"),
        related_name="occupancy",
        on_delete=models.CASCADE,
    )
    current = models.PositiveIntegerField(_("current"), default=0)
    maximum = models.PositiveIntegerField(_("maximum"), default=0)

    class Meta:
        verbose_name = _("course capacity")
        verbose_name_plural = _("course capacity")

    def __str__(self):
        return str(self.course_id)


class CourseGroup(
    AvailabilityMixin, CourseSettings, TimeStampedModel, HrdbIdModelMixin
):
    begin_date_field = "begin_date"
    end_date_field = "end_date"
    enroll_begin_field = "enroll_begin"
    enroll_end_field = "enroll_end"

    hrdb_id = models.IntegerField(
        _("HRDB ID"),
        blank=True,
        null=True,
        unique=True,
        help_text=_("Identifier in HRDB"),
    )

    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="groups",
        on_delete=models.PROTECT,
    )
    slug = models.SlugField(_("code"), max_length=255, blank=True)
    name = models.CharField(_("name"), max_length=255)
    summary = models.CharField(_("short description"), max_length=2048, blank=True)

    is_active = models.BooleanField(_("active"), default=True)
    can_join = models.BooleanField(_("enrollment allowed"), default=True)

    num_participants = models.PositiveIntegerField(
        _("number of participants"), default=0, editable=False
    )
    max_participants = models.PositiveIntegerField(
        _("maximum number of participants"), default=0
    )

    members = models.ManyToManyField(
        User,
        verbose_name=_("participants"),
        related_name="group",
        blank=True,
    )

    objects = CourseGroupManager.from_queryset(CourseGroupQuerySet)()

    tracker = FieldTracker(
        fields=["num_participants", "max_participants", "enroll_begin", "enroll_end"]
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ("begin_date", "name")
        verbose_name = _("student group")
        verbose_name_plural = _("student groups")
        permissions = (
            ("import_coursegroup", _("Can import course groups")),
            ("export_coursegroup", _("Can export course groups")),
        )

    def __str__(self):
        return f"{self.name} [{self.slug}]" if self.slug else self.name

    def delete(self, *args, **kwargs):
        if self.has_passed_students:
            raise ValidationError(
                _("cannot delete a group containing students who completed the course"),
                code="invalid",
            )

        for student in self.students.filter(status=CourseStudent.StatusChoices.ACTIVE):
            student.status = CourseStudent.StatusChoices.EXPELLED
            student.substatus = CourseStudent.StudySubstatusChoices.CANCELLED
            student._change_reason = _("expulsion caused by group deletion")
            student.save()

        from lms.enrollments.models import EnrolledUser

        for enrolled_user in self.enrolled_users.filter(
            status=EnrolledUser.StatusChoices.PENDING
        ):
            enrolled_user.reject(change_reason=_("rejection caused by group deletion"))

        return super(CourseGroup, self).delete(*args, **kwargs)

    @property
    def was_full(self):
        prev_num_participants = self.tracker.previous("num_participants") or 0
        prev_max_participants = self.tracker.previous("max_participants") or 0
        return (
            prev_max_participants != 0
            and prev_num_participants == prev_max_participants
        )

    @property
    def become_not_full_again(self) -> bool:
        return (
            (
                self.tracker.has_changed("num_participants")
                or self.tracker.has_changed("max_participants")
            )
            and self.was_full
            and not self.is_full
        )

    @property
    def become_available_again(self):
        return self.become_not_full_again and self.available_for_enroll

    def get_current_capacity(self):
        return self.num_participants

    def get_maximum_capacity(self):
        return self.max_participants

    def get_group_or_course_field(self, field_name):
        return getattr(self, field_name, None) or getattr(self.course, field_name, None)

    def enroll_open_for_dates(self, enroll_begin, enroll_end, now=None) -> bool:
        # Empty enrollment dates mean that group enrollment is closed, unlike a
        # course where empty dates mean no restrictions.
        if enroll_begin is None and enroll_end is None:
            return False

        return super().enroll_open_for_dates(enroll_begin, enroll_end, now=now)

    def check_enroll_open(self, now=None) -> bool:
        """
        Check whether group enrollment is open at the given time.
        Date checks are centralized here after being moved from CourseSettings.
        """
        return self.enroll_open_for_dates(self.enroll_begin, self.enroll_end, now=now)

    @property
    def available_by_dates_now(self):
        return self.check_enroll_open()

    @property
    def is_full(self) -> bool:
        return self.is_enroll_open and (
            self.max_participants != 0
            and self.num_participants >= self.max_participants
        )

    @property
    def available(self):
        return self.is_active and self.can_join

    @property
    def available_for_enroll(self) -> bool:
        return self.can_join and super().available_for_enroll

    @property
    def has_students(self):
        return self.students.exists()

    @property
    def has_passed_students(self):
        return self.students.filter(
            status=CourseStudent.StatusChoices.COMPLETED
        ).exists()

    @property
    def has_enrolled_users(self):
        return self.enrolled_users.exists()

    @property
    def is_enroll_open(self) -> bool:
        return self.available and self.check_enroll_open()

    @property
    def enroll_will_begin(self) -> Optional[datetime]:
        if not self.is_active:
            return None

        now = timezone.now().replace(second=0, microsecond=0)
        if self.enroll_begin is not None and self.enroll_begin > now:
            return self.enroll_begin

        return None


class CourseStudent(TimeStampedModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Active")
        EXPELLED = "expelled", _("Expelled")
        COMPLETED = "completed", _("Completed training")

    class StudySubstatusChoices(models.TextChoices):
        CANCELLED = "education_canceled", _("education cancelled")
        INTERRUPTED = "study_interrupted", _("study interrupted")
        DISMISSED = "dismissed", _("dismissed")
        SUCCESS = "success", _("successful")
        FAILURE = "failure", _("unsuccessful")

    ENROLLS_STATUS_CHOICES = [
        (StatusChoices.ACTIVE.value, StatusChoices.ACTIVE.label),
        (StatusChoices.COMPLETED.value, StatusChoices.COMPLETED.label),
    ]

    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="students",
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        related_name="in_courses",
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        CourseGroup,
        verbose_name=_("group"),
        related_name="students",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    completion_date = models.DateTimeField(
        _("course completion date"), null=True, blank=True
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )
    substatus = models.CharField(
        _("substatus"),
        max_length=20,
        choices=StudySubstatusChoices.choices,
        blank=True,
    )
    is_visible = models.BooleanField(
        _("Visibility"),
        help_text=_("Whether the user has hidden the course"),
        default=True,
    )
    is_passed = models.BooleanField(_("passing score achieved"), default=False)
    passing_date = models.DateTimeField(
        _("course completion date"),
        help_text=_("time when the student achieved the passing score"),
        null=True,
        blank=True,
    )
    is_required = models.BooleanField(_("is mandatory"), default=False)
    required_since = models.DateTimeField(
        _("course assignment date"),
        help_text=_("time when the course became mandatory for the student"),
        null=True,
        blank=True,
    )

    tracker = FieldTracker(fields=["status", "is_passed"])

    objects = CourseStudentQuerySet.as_manager()

    history = HistoricalRecords()

    class Meta:
        ordering = ("-created",)
        verbose_name = _("student")
        verbose_name_plural = _("students")

    def __str__(self):
        return f"User: {self.user_id} Course: {self.course_id} Group: {self.group_id}"

    def save(self, *args, **kwargs):
        self.full_clean()
        self._update_dates()
        super().save(*args, **kwargs)

    def _update_dates(self) -> None:
        if self.is_required and not self.required_since:
            self.required_since = timezone.now()

        if self.is_passed and not self.passing_date:
            self.passing_date = timezone.now()

        if self.status == self.StatusChoices.COMPLETED and not self.completion_date:
            self.completion_date = timezone.now()

    def expell(self, change_reason: str = None) -> None:
        if change_reason:
            self._change_reason = change_reason

        self.status = self.StatusChoices.EXPELLED
        self.save()

    def complete(self, change_reason: str = None) -> None:
        if change_reason:
            self._change_reason = change_reason

        self.status = self.StatusChoices.COMPLETED
        self.save()

    def pass_course(self) -> None:
        if not self.is_passed:
            self.is_passed = True
            self.status = self.StatusChoices.COMPLETED
            self.substatus = self.StudySubstatusChoices.SUCCESS
            self.save()

    @property
    def can_complete_by_student(self) -> bool:
        """Whether the user can complete this course independently."""
        course = self.course
        if (
            course.structure == Course.StructureChoices.NO_MODULES
            and self.status == self.StatusChoices.ACTIVE
        ):
            return True

        return False

    def can_be_hidden(self, *, raise_exception: bool = True) -> bool:
        """Whether all conditions for hiding this course have been met."""
        errors = {}
        if self.is_required and not self.is_passed:
            errors["required"] = _("The mandatory course has not been completed.")
        if errors and raise_exception:
            raise ValidationError(errors)
        return not bool(errors)

    def set_course_visibility(
        self, *, visible: bool, validate: bool = True, commit: bool = True
    ) -> None:
        if not visible and validate:
            self.can_be_hidden(raise_exception=True)

        self.is_visible = visible
        if commit:
            self.save()

    def clean(self):
        if self.course.course_type == Course.TypeChoices.OTHER:
            return

        if self._state.adding:
            current_student = CourseStudent.get_current_student(
                course=self.course,
                user=self.user,
            )
            if current_student:
                # Report an error when an unfinished enrollment exists.
                if current_student.status == CourseStudent.StatusChoices.ACTIVE:
                    raise ValidationError(
                        _("there is an unfinished enrollment"),
                        code="invalid",
                    )

                # Report an error when course retakes are not allowed.
                if not self.course.retries_allowed:
                    raise ValidationError(
                        _("course retake is not allowed"),
                        code="invalid",
                    )

    def get_progress_score(self, default=None):
        progress = next(iter(self.course_progresses.all()), None)
        if not progress:
            return default
        return progress.score

    @property
    def is_finished(self) -> bool:
        return self.is_passed or self.status == CourseStudent.StatusChoices.COMPLETED

    @property
    def finished_date(self) -> datetime | None:
        if self.completion_date:
            return self.completion_date
        if self.passing_date:
            return self.passing_date

    @classmethod
    def get_current_student(cls, user: User | int, course: Course | int):
        return cls.objects.filter(user=user, course=course).order_by("-id").first()


class CourseBlock(OrderedModel, TimeStampedModel):
    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="blocks",
        on_delete=models.PROTECT,
    )
    name = models.CharField(_("name"), max_length=255, blank=True, default="")
    summary = models.CharField(_("short description"), max_length=2048, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    order_with_respect_to = "course"

    objects = CourseBlockQuerySet.as_manager()

    class Meta(OrderedModel.Meta):
        verbose_name = _("course block")
        verbose_name_plural = _("course blocks")

    def __str__(self):
        return self.name


class CourseModule(OrderedModel, TimeStampedModel, BaseModule):
    module_type = models.ForeignKey(
        "moduletypes.ModuleType",
        verbose_name=_("module type"),
        related_name="modules",
        editable=False,
        on_delete=models.PROTECT,
    )
    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="modules",
        on_delete=models.PROTECT,
    )
    block = models.ForeignKey(
        CourseBlock,
        verbose_name=_("block"),
        related_name="modules",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    estimated_time = models.PositiveSmallIntegerField(
        _("estimated completion time"),
        null=True,
        blank=True,
        help_text=_("estimated course completion time (minutes)"),
    )

    weight = models.PositiveSmallIntegerField(
        _("weight"),
        default=0,
        validators=[MaxValueValidator(100)],
    )
    weight_scaled = models.DecimalField(
        _("absolute weight share"),
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MaxValueValidator(1), MinValueValidator(0)],
        help_text=_("calculated automatically from the weights of all course modules"),
    )

    field_tracker = FieldTracker(fields=["weight", "is_active", "estimated_time"])

    order_with_respect_to = "course"

    # noinspection PyUnresolvedReferences
    order_class_path = f"{__module__}.CourseModule"

    objects = CourseModuleQuerySet.as_manager()

    class Meta(OrderedModel.Meta):
        verbose_name = _("course module")
        verbose_name_plural = _("course modules")

        ordering = ("block__order", "order")

    def set_default_weight(self):
        if not self._state.adding or settings.COURSE_MODULE_DEFAULT_WEIGHT < 0:
            return
        self.weight = min(100, settings.COURSE_MODULE_DEFAULT_WEIGHT)

    def complete(self, student: CourseStudent):
        self.update_progress(student=student, value=100)

    def update_progress(self, student: CourseStudent, value: int, force: bool = False):
        from courses.services import update_module_progress

        update_module_progress(module=self, student=student, value=value, force=force)

    def delete_student_progress(self, *, student: CourseStudent, **kwargs):
        """
        Delete all student data for the module.
        """
        self.remove_progress(student=student)

    def remove_progress(self, student: CourseStudent):
        from courses.services import remove_module_progress

        remove_module_progress(student=student, module=self)

    def is_score_threshold_reached(self, score: int) -> bool:
        completion_threshold = 100
        return score >= completion_threshold

    def clean(self):
        if self.block is not None and self.block.course != self.course:
            raise ValidationError(
                _("the block course must match the module course"),
                code="invalid",
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        self.set_default_weight()
        return super().save(*args, **kwargs)

    def get_display_name(self) -> str:
        return self.name

    def __str__(self):
        return self.name


class StudentCourseState(TimeStampedModel):
    student = models.OneToOneField(
        CourseStudent,
        verbose_name=_("Student"),
        related_name="student_course_state",
        on_delete=models.CASCADE,
    )
    # Denormalized for fast lookup.
    course = models.ForeignKey(
        Course,
        verbose_name=_("Course"),
        related_name="student_course_states",
        on_delete=models.PROTECT,
    )
    last_visited_module = models.PositiveIntegerField(
        _("Last opened module"), blank=True, null=True
    )
    state = models.JSONField(_("State"), default=dict, blank=True)
    cache = models.JSONField("Cache", default=dict, blank=True)

    tracker = FieldTracker(fields=["last_visited_module"])

    class CompleteAllModulesModalShown(models.TextChoices):
        DISABLED = "disabled", _("Disabled")
        ENABLED = "enabled", _("Enabled")
        COMPLETED = "completed", _("Completed")

    complete_all_modules_modal_shown = models.CharField(
        _("Course completion dialog status"),
        max_length=20,
        choices=CompleteAllModulesModalShown.choices,
        default=CompleteAllModulesModalShown.DISABLED,
    )
    need_ask_language = models.BooleanField(
        _("Need to ask for the study language"),
        null=True,
        blank=True,
        default=False,
    )

    class Meta:
        verbose_name = _("Course completion state")
        verbose_name_plural = _("Course completion states")

    def clean(self):
        if self.student.course_id != self.course_id:
            raise ValidationError(
                _("the student's course must match the state course"),
                code="invalid",
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class StudentCourseProgress(TimeStampedModel):
    student = models.ForeignKey(
        CourseStudent,
        verbose_name=_("student"),
        related_name="course_progresses",
        on_delete=models.PROTECT,
    )
    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="course_progresses",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
    )
    score = models.PositiveSmallIntegerField(
        _("scores"), default=0, validators=[MaxValueValidator(100)]
    )
    history = HistoricalRecords(excluded_fields=["created", "student", "course"])

    tracker = FieldTracker(fields=["score"])

    def is_course_passed(self):
        return self.score >= self.course.completion_threshold

    def save(self, *args, **kwargs):
        if not self.course_id:
            self.course_id = self.student.course_id
        if (
            self._state.adding or self.tracker.has_changed("score")
        ) and self.is_course_passed():
            self.student.pass_course()
        return super().save(*args, **kwargs)

    def __str__(self):
        return _("Student {} progress for course {}").format(
            self.student_id, self.course_id
        )

    class Meta:
        verbose_name = _("course progress")
        verbose_name_plural = _("course progress records")
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course"
            )
        ]


class StudentModuleProgress(TimeStampedModel):
    student = models.ForeignKey(
        CourseStudent,
        verbose_name=_("student"),
        related_name="module_progresses",
        on_delete=models.PROTECT,
    )
    course = models.ForeignKey(
        Course,
        verbose_name=_("course"),
        related_name="module_progresses",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
    )
    module = models.ForeignKey(
        CourseModule,
        verbose_name=_("module"),
        related_name="progresses",
        on_delete=models.PROTECT,
    )
    score = models.PositiveSmallIntegerField(
        _("scores"),
        default=0,
        validators=[MaxValueValidator(100)],
    )
    score_scaled = models.DecimalField(
        _("weighted scores"),
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
    )
    passing_date = models.DateTimeField(
        _("module completion date"),
        null=True,
        blank=True,
    )
    is_set_attendance = models.BooleanField(
        _("attendance recorded"), null=True, blank=True
    )

    tracker = FieldTracker(fields=["score"])

    def clean(self):
        if self.student.course_id != self.module.course_id:
            raise ValidationError(
                _("the student's course must match the module course"),
                code="invalid",
            )

    def update_passing_date(self):
        if not self.passing_date and self.module.is_score_threshold_reached(self.score):
            self.passing_date = timezone.now()

    def save(self, *args, **kwargs):
        if not self.course_id:
            self.course = self.student.course
        self.update_passing_date()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return _("Student {} progress for module {}").format(
            self.student_id, self.module_id
        )

    class Meta:
        verbose_name = _("module progress")
        verbose_name_plural = _("module progress records")
        constraints = [
            models.UniqueConstraint(
                fields=["student", "module"], name="unique_student_module"
            )
        ]


class CourseBookmark(BookmarkAuthor, Bookmark):
    BOOKMARK_TYPE = "course"

    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created by"),
        related_name="+",
        on_delete=models.CASCADE,
    )

    course = models.ForeignKey(
        Course,
        verbose_name=_("Course"),
        related_name="bookmarks",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Bookmarks: Course")
        verbose_name_plural = _("Bookmarks: Courses")
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "course"],
                name="unique_course_bookmark_per_user",
            )
        ]

    def __str__(self):
        return (
            f"CourseBookmark: "
            f"course_id={self.course_id} user_id={self.created_by_id}"
        )
