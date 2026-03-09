from django.contrib import admin
from .models import Formation, Module, Lesson, Enrollment, LessonProgress


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    ordering = ['order']


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ['order']


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'price', 'duration', 'is_active', 'created_at')
    list_filter = ('level', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'prerequisites', 'program')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_active', 'price')
    date_hierarchy = 'created_at'
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'formation', 'order', 'is_free')
    list_filter = ('formation', 'is_free')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'lesson_type', 'duration_minutes')
    list_filter = ('lesson_type', 'module__formation')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'formation', 'enrolled_at', 'is_active')
    list_filter = ('is_active', 'formation')
    readonly_fields = ('enrolled_at',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed',)
    readonly_fields = ('user', 'lesson', 'completed', 'completed_at')
