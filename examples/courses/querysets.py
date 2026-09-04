import operator
from functools import reduce
from typing import Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.module_loading import import_string
from ordered_model.models import OrderedModelQuerySet

from lms.core.models.mixins import ActiveFilterMixin

from .mixins import AvailableQuerySetMixin, PermissionQuerySetMixin

User = get_user_model()


class StudyModeQuerySet(ActiveFilterMixin, OrderedModelQuerySet):
    pass


class CourseCategoryQuerySet(ActiveFilterMixin, models.QuerySet):
    def _get_categories_with_courses_ids(self):
        return self.model.categories.through.objects.values_list(
            "coursecategory_id", flat=True
        )

    def with_courses(self) -> bool:
        return self.filter(id__in=self._get_categories_with_courses_ids())

    def without_courses(self) -> bool:
        return self.exclude(id__in=self._get_categories_with_courses_ids())


class CoursePermittedQuerySet(PermissionQuerySetMixin, models.QuerySet):
    def permitted(self, permission: Union[str, Permission], user: User):
        if user.is_superuser:
            return self
        user_arg_name = "courseuserobjectpermission__permission"
        group_arg_name = "coursegroupobjectpermission__permission"
        if isinstance(permission, str):
            user_arg_name += "__codename"
            group_arg_name += "__codename"
            _, user_arg_val = permission.split(".")
            group_arg_val = user_arg_val
        else:
            user_arg_val = permission
            group_arg_val = permission
        filters = Q(
            courseuserobjectpermission__user=user, **{user_arg_name: user_arg_val}
        ) | Q(
            coursegroupobjectpermission__group__user=user,
            **{group_arg_name: group_arg_val},
        )
        return self.filter(
            Q(id__in=self.model.objects.filter(filters)) | Q(author=user)
        )


class CourseQuerySet(AvailableQuerySetMixin, PermissionQuerySetMixin, models.QuerySet):
    maximum_capacity_field = "occupancy__maximum"
    current_capacity_field = "occupancy__current"
    capacity_field = "occupancy"

    enroll_begin_field = "calc_enroll_begin"
    enroll_end_field = "calc_enroll_end"

    def active(self, user=None, preview=False):
        qs = self.filter(is_archive=False)
        if not preview:
            return qs.filter(is_active=True)
        view_permission = self.get_default_permission("view")
        if user and user.has_perm(view_permission):
            return qs

        qs_active = qs.filter(is_active=True)
        qs_author = qs.filter(author=user)
        qs_group_permitted = qs.filter(
            coursegroupobjectpermission__permission__codename="view_course",
            coursegroupobjectpermission__permission__content_type__app_label=self.model._meta.app_label,
            coursegroupobjectpermission__permission__content_type__model=self.model._meta.model_name,
            coursegroupobjectpermission__content_object=F("id"),
            coursegroupobjectpermission__group__user=user,
        )
        qs_user_permitted = qs.filter(
            courseuserobjectpermission__permission__codename="view_course",
            courseuserobjectpermission__permission__content_type__app_label=self.model._meta.app_label,
            courseuserobjectpermission__permission__content_type__model=self.model._meta.model_name,
            courseuserobjectpermission__content_object=F("id"),
            courseuserobjectpermission__user=user,
        )

        return qs.filter(
            Q(id__in=qs_active)
            | Q(id__in=qs_author)
            | Q(id__in=qs_group_permitted)
            | Q(id__in=qs_user_permitted)
        )

    def permitted(self, permission: Union[str, Permission], user: User):
        permitted_qs_list = [
            import_string(qs)(model=self.model).permitted(permission, user)
            for qs in settings.COURSE_PERMITTED_QUERYSETS
        ]
        return self.filter(id__in=reduce(operator.or_, permitted_qs_list))


class CourseWorkflowQuerySet(ActiveFilterMixin, models.QuerySet):
    pass


class CourseGroupQuerySet(AvailableQuerySetMixin, ActiveFilterMixin, models.QuerySet):
    maximum_capacity_field = "max_participants"
    current_capacity_field = "num_participants"
    capacity_field = None

    enroll_begin_field = "enroll_begin"
    enroll_end_field = "enroll_end"

    def available(self):
        return self.filter(is_active=True, can_join=True)

    def opened(self, now=None):
        if now is None:
            now = timezone.now().replace(second=0, microsecond=0)

        return self.available().filter(
            ~Q(enroll_begin__isnull=True, enroll_end__isnull=True)
            & (
                (Q(enroll_begin__lte=now) | Q(enroll_begin__isnull=True))
                & (Q(enroll_end__gte=now) | Q(enroll_end__isnull=True))
            )
        )

    def available_by_dates_now(self):
        now = timezone.now().replace(second=0, microsecond=0)
        return self.filter(
            ~Q(
                **{
                    f"{self.enroll_begin_field}__isnull": True,
                    f"{self.enroll_end_field}__isnull": True,
                }
            )
            & (
                (
                    Q(**{f"{self.enroll_begin_field}__lte": now})
                    | Q(**{f"{self.enroll_begin_field}__isnull": True})
                )
                & (
                    Q(**{f"{self.enroll_end_field}__gte": now})
                    | Q(**{f"{self.enroll_end_field}__isnull": True})
                )
            )
        )

    def available_by_dates_gte_now(self):
        now = timezone.now().replace(second=0, microsecond=0)
        return self.filter(
            Q(**{f"{self.enroll_end_field}__isnull": True})
            | Q(**{f"{self.enroll_end_field}__gte": now})
        )

    def available_for_view(self):
        return self.filter(can_join=True).available_by_dates_gte_now()

    def available_for_enroll(self):
        return super().available_for_enroll().filter(can_join=True)


class CourseStudentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=self.model.StatusChoices.ACTIVE)


class CourseModuleQuerySet(ActiveFilterMixin, OrderedModelQuerySet):
    pass


class CourseBlockQuerySet(ActiveFilterMixin, OrderedModelQuerySet):
    pass
