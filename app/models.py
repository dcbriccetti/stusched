import re
from datetime import date, datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
import markdown

DAYS_PER_YEAR = 365.24


class Timestamped(models.Model):
    added = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True

class Course(Timestamped):
    name = models.CharField(max_length=100)
    url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name.__str__()

STATUSES = ((1, 'Proposed'), (2, 'Accepting'), (3, 'Scheduled'))


class Section(Timestamped):
    start_time = models.DateTimeField()
    hours_per_day = models.DecimalField(max_digits=4, decimal_places=2)
    num_days = models.IntegerField(default=1)
    course = models.ForeignKey(Course)
    price = models.IntegerField(null=True, blank=True)
    min_students = models.IntegerField(default=3)
    max_students = models.IntegerField(default=6)
    scheduled_status = models.IntegerField(choices=STATUSES)
    notes = models.TextField(blank=True)
    private_notes = models.TextField(blank=True)

    def __str__(self):
        return '%s %s' % (self.start_time, self.course.name)

    def has_passed(self):
        return datetime.now() > self.start_time

    def scheduled_status_string(self):
        return '' if self.has_passed() else [st[1] for st in STATUSES if st[0] == self.scheduled_status][0]

    def registration_open(self):
        return not self.has_passed()  # Todo is it full?

    def num_students(self):
        return self.student_set.count()

    def students(self):
        return ', '.join((s.name for s in self.student_set.all().order_by('name')))

    def students_sorted(self):
        return self.student_set.all().order_by('name')

    def hours_per_day_formatted(self):
        hpd = str(self.hours_per_day)
        return hpd[:-3] if hpd.endswith('.00') else hpd

    def when(self):
        date_part = self.start_time.strftime('%a, %b %d, ’%y')
        if (self.num_days > 1):
            date_part2 = (self.start_time + timedelta(days=int(self.num_days))).strftime('%b %d')
            date_part += '–' + date_part2
        def time_fmt(minute): return '%I %p' if minute == 0 else '%I:%M %p'
        end_time = self.start_time + timedelta(minutes=int(self.hours_per_day * 60))
        result = '%s, %s–%s' % (date_part, self.start_time.strftime(time_fmt(self.start_time.minute)),
            end_time.strftime(time_fmt(end_time.minute)))
        result = re.compile('0+(\d)').sub('\g<1>', result)  # Remove leading zeroes
        for ap in ('AM', 'PM'):
            result = re.compile('(.*)( {0})(.*)( {0})'.format(ap)).sub('\g<1>\g<3>\g<4>', result)  # Remove redundant AM/PM
        return result


class Parent(Timestamped):
    name = models.CharField(max_length=100, help_text='Full name of one or more parents.')
    phone = models.CharField(max_length=100, null=True, blank=True, help_text='Used for emergency contact or by prior arrangement.')
    email = models.EmailField(null=True, blank=True)
    referred_by = models.CharField(max_length=200, null=True, blank=True, help_text='How you heard of Dave B’s Young Programmers: A person’s name, web search, Facebook, Meetup, etc.')
    private_notes = models.TextField(blank=True)
    code  = models.CharField(max_length=100, null=True, blank=True)
    # Set via: update app_parent set code = md5(random()::text) where code = '';
    users = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.name.__str__()

    def user(self):
        return ', '.join((user.username for user in self.users.all()))

    def active(self):
        return self.student_set.filter(active=True).count() > 0

    def students_sorted(self):
        return self.student_set.all().order_by('name')

    @property
    def has_upcoming(self):
        return self.student_set.filter(sections__start_time__gt=datetime.now()).count() > 0

    active.boolean = True


class Student(Timestamped):
    name            = models.CharField(max_length=100, help_text='The student’s full name.')
    active          = models.BooleanField(default=True)
    birthdate       = models.DateField(null=True, blank=True, help_text='Used so the system always knows the student’s current age.')
    grade_from_age  = models.IntegerField(null=True, blank=True,
        help_text='The number to subtract from the student’s age on September 1st to calculate the grade (usually 5).')
    school          = models.CharField(max_length=100, null=True, blank=True, help_text='This is nice for the teacher to know, but isn’t required.')
    parent          = models.ForeignKey(Parent)
    email           = models.EmailField(null=True, blank=True, help_text='This makes it more convenient for the teacher to communicate with the student, but isn’t required.')
    aptitude        = models.IntegerField(null=True, blank=True)
    sections        = models.ManyToManyField(Section, blank=True, through='StudentSectionAssignment')
    wants_courses   = models.ManyToManyField(Course, blank=True, help_text='Select zero or more.')
    when_available  = models.TextField(blank=True, help_text='Used in planning new course sections.')
    notes           = models.TextField(blank=True, help_text='Background on the student, including any previous programming experience; allergies, special emergency instructions, etc.')
    private_notes   = models.TextField(blank=True)

    def age(self):
        years = self.age_years()
        return "%.2f" % years if years else ''

    def age_conventional(self):
        years = self.age_years()
        return "%d" % years if years else ''

    def age_years(self):
        today = date.today()
        return (today - self.birthdate).days / DAYS_PER_YEAR if self.birthdate else None

    def grade(self):
        if not self.birthdate: return ''
        today = date.today()
        current_school_year_starting_year = today.year if today.month >= 7 else today.year - 1
        sep1 = date(current_school_year_starting_year, 9, 1)
        age_years_sep1 = int((sep1 - self.birthdate).days / DAYS_PER_YEAR)
        grade = str(age_years_sep1 - self.grade_from_age) if self.grade_from_age else '%d?' % (age_years_sep1 - 5)
        return grade

    def sections_taken(self):
        return ', '.join([section.course.name for section in self.sections.all().order_by('course__name')])

    def courses_wanted(self):
        return ', '.join([course.name for course in self.wants_courses.all().order_by('name')])

    def __str__(self):
        return self.name.__str__()


class KnowledgeItem(Timestamped):
    name        = models.CharField(max_length=100)
    students    = models.ManyToManyField(Student, through='Knows')

    def __str__(self):
        return self.name.__str__()


class Knows(Timestamped):
    student     = models.ForeignKey(Student, on_delete=models.CASCADE)
    item        = models.ForeignKey(KnowledgeItem, on_delete=models.CASCADE)
    quantity    = models.IntegerField()

    def __str__(self):
        return '%s %s %d' % (self.student.name, self.item.name, self.quantity)


SS_STATUS_APPLIED  = 1
SS_STATUS_ACCEPTED = 2
SS_STATUS_REJECTED = 3
SS_STATUSES = ((SS_STATUS_APPLIED, 'Applied'), (SS_STATUS_ACCEPTED, 'Accepted'), (SS_STATUS_REJECTED, 'Rejected'))
SS_STATUSES_BY_ID = {item[0]: item[1] for item in SS_STATUSES}


class StudentSectionAssignment(Timestamped):
    class Meta:
        db_table = 'app_student_section'

    student     = models.ForeignKey(Student, on_delete=models.CASCADE)
    section     = models.ForeignKey(Section, on_delete=models.CASCADE)
    status      = models.IntegerField(choices=SS_STATUSES)
    applied_time= models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s %s' % (self.student.name, str(self.section))

    def status_str(self):
        return SS_STATUSES_BY_ID[self.status]


class AugmentedSsa:
    'Provide a StudentSectionAssignment along with whether the student is waitlisted'
    def __init__(self, ssa, waitlisted):
        self.ssa = ssa
        self.waitlisted = waitlisted

def augmented_student_section_assignments(section_id):
    'Return AugmentedSsa objects for a section'
    ssas = StudentSectionAssignment.objects.filter(section_id=section_id).order_by('applied_time').select_related('section', 'student')
    return [AugmentedSsa(ssa, seq >= ssa.section.max_students) for seq, ssa in enumerate(ssas)]

class NewsItem(Timestamped):
    title = models.CharField(max_length=200, blank=True, null=True)
    text = models.TextField()  # Markdown text

    def as_html(self):
        return markdown.markdown(self.text)
