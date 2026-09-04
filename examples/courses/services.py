from .models import CourseModule, CourseStudent, StudentModuleProgress


def update_module_progress(
    *,
    module: CourseModule,
    student: CourseStudent,
    value: int,
    force: bool = False,
) -> StudentModuleProgress:
    progress, created = StudentModuleProgress.objects.get_or_create(
        module=module,
        student=student,
        defaults={"score": value},
    )
    if not created and (force or value > progress.score):
        progress.score = value
        progress.save(update_fields=["score", "modified"])
    return progress


def remove_module_progress(*, module: CourseModule, student: CourseStudent) -> None:
    StudentModuleProgress.objects.filter(module=module, student=student).delete()
