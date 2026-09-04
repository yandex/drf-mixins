import warnings
from functools import cached_property
from typing import Literal

from django.db import models
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AvailabilityMixin:
    """
    Override the names of fields that store the data before using this mixin.
    For example:
        begin_date_field = "calc_begin_date"
    """

    begin_date_field = None
    end_date_field = None
    enroll_begin_field = None
    enroll_end_field = None

    STATUS_AVAILABLE = "available"
    STATUS_UNAVAILABLE = "unavailable"
    STATUS_NO_VACANCY = "no_vacancy"

    STATUS_CHOICES = (
        (STATUS_AVAILABLE, _("Available")),
        (STATUS_UNAVAILABLE, _("Unavailable")),
        (STATUS_NO_VACANCY, _("No vacancies")),
    )

    def get_group_or_course_field(self, field_name: str):
        raise NotImplementedError("get_group_or_course_field() must be implemented.")

    def get_begin_date(self):
        return self.get_group_or_course_field(self.begin_date_field)

    def get_end_date(self):
        return self.get_group_or_course_field(self.end_date_field)

    def get_enroll_begin(self):
        return self.get_group_or_course_field(self.enroll_begin_field)

    def get_enroll_end(self):
        return self.get_group_or_course_field(self.enroll_end_field)

    @property
    def available_by_dates_now(self):
        enroll_begin = self.get_enroll_begin()
        enroll_end = self.get_enroll_end()
        if enroll_begin is not None and enroll_begin > timezone.now():
            return False

        if enroll_end is not None and enroll_end < timezone.now():
            return False

        return True

    @cached_property
    def available_for_enroll(self) -> bool:
        return self.is_active and not self.is_full and self.available_by_dates_now

    def get_current_capacity(self):
        raise NotImplementedError()

    def get_maximum_capacity(self):
        raise NotImplementedError()

    @property
    def status(self):
        warnings.warn(
            "`AvailabilityMixin.status` property is deprecated",
            DeprecationWarning,
            stacklevel=2,
        )

        enroll_begin = self.get_enroll_begin()
        enroll_end = self.get_enroll_end()
        now = timezone.now()

        if enroll_begin and enroll_begin > now:
            return self.STATUS_UNAVAILABLE

        if enroll_end and enroll_end < now:
            return self.STATUS_UNAVAILABLE

        current_capacity = self.get_current_capacity()
        maximum_capacity = self.get_maximum_capacity()
        if current_capacity is not None and 0 < maximum_capacity <= current_capacity:
            return self.STATUS_NO_VACANCY

        return self.STATUS_AVAILABLE


class CapacityQuerySetMixin(models.QuerySet):
    maximum_capacity_field = None
    current_capacity_field = None
    capacity_field = None

    def not_full(self):
        filter_args = Q(**{self.maximum_capacity_field: 0}) | Q(
            **{f"{self.current_capacity_field}__lt": F(self.maximum_capacity_field)}
        )

        if self.capacity_field is not None:
            filter_args |= Q(**{f"{self.capacity_field}__isnull": True})

        return self.filter(filter_args)


class AvailableQuerySetMixin(CapacityQuerySetMixin):
    """
    Override the names of fields that store the data before using this mixin.
    For example:
        maximum_capacity_field = "occupancy__maximum"
    """

    enroll_begin_field = None
    enroll_end_field = None

    def available_by_dates_now(self):
        now = timezone.now().replace(second=0, microsecond=0)
        return self.filter(
            Q(
                **{
                    f"{self.enroll_begin_field}__isnull": True,
                    f"{self.enroll_end_field}__isnull": True,
                }
            )
            | Q(
                **{
                    f"{self.enroll_begin_field}__lte": now,
                    f"{self.enroll_end_field}__isnull": True,
                }
            )
            | Q(
                **{
                    f"{self.enroll_begin_field}__lte": now,
                    f"{self.enroll_end_field}__gte": now,
                }
            )
            | Q(
                **{
                    f"{self.enroll_begin_field}__isnull": True,
                    f"{self.enroll_end_field}__gte": now,
                }
            )
        )

    def available_for_enroll(self):
        return self.available_by_dates_now().not_full()


class PermissionQuerySetMixin(models.QuerySet):
    def get_default_permission(
        self, permission: Literal["add", "change", "delete", "view"]
    ):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name

        return f"{app_label}.{permission}_{model_name}"
