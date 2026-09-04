from django.db import models, transaction
from django.dispatch import receiver

from .models import Course, CourseOccupancy


@receiver(signal=models.signals.post_save, sender=Course)
def course_post_save_handler(instance: Course, **kwargs):
    transaction.on_commit(
        lambda: CourseOccupancy.objects.get_or_create(course=instance)
    )
