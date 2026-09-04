from django.contrib import admin

from . import models

admin.site.register(
    [
        models.StudyMode,
        models.CourseCategory,
        models.Course,
        models.CourseProgram,
        models.CourseTutor,
        models.CourseTeacher,
        models.CourseOccupancy,
        models.CourseGroup,
        models.CourseStudent,
        models.CourseBlock,
        models.CourseModule,
        models.StudentCourseState,
        models.StudentCourseProgress,
        models.StudentModuleProgress,
        models.CourseBookmark,
    ]
)
