from django.contrib import admin
from .models import *


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


class StudentsInSectionInline(admin.TabularInline):
    model = Student.sections.through


class ParentAdmin(admin.ModelAdmin):
    ordering = ('name',)
    list_display = ('name', 'user', 'active', 'added', 'updated', 'phone', 'email', 'referred_by', 'private_notes')
    search_fields = ('name',)
    inlines = [StudentInline]


class KnowsInline(admin.TabularInline):
    model = Knows
    extra = 0


class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'parent', 'birthdate', 'age', 'grade', 'notes', 'private_notes',
                    'sections_taken', 'courses_wanted', 'when_available')
    ordering = ('name',)
    search_fields = ('name',)
    inlines = [KnowsInline]


class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'start_time', 'num_students', 'students', 'hours_per_day',
                    'num_days', 'price', 'notes', 'private_notes')
    ordering = ('-start_time',)
    search_fields = ('course__name',)
    inlines = [StudentsInSectionInline]


class KnowsAdmin(admin.ModelAdmin):
    list_display = ('student', 'item', 'quantity')
    ordering = ('student', 'item')
    search_fields = ('student__name', 'item__name')


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'url')
    ordering = ('name',)
    search_fields = ('name',)
    inlines = (SectionInline,)


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated', 'text')

admin.site.register(Course,  CourseAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Parent,  ParentAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Knows,   KnowsAdmin)
admin.site.register(KnowledgeItem)
admin.site.register(NewsItem, NewsItemAdmin)
