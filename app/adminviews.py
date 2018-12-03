import logging
import random
from datetime import datetime
from django.core import mail
from django.http import Http404
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.views.generic import View
from django.core.mail import EmailMultiAlternatives
import html2text
from app.models import Parent, Student, Section, StudentSectionAssignment, SS_STATUS_APPLIED, SS_STATUS_ACCEPTED, \
    NewsItem
from app.sections import SectionRows

log = logging.getLogger(__name__)


class Admin(View):
    def get(self, request):
        if not request.user.is_staff:
            raise Http404

        status = (
            ('Parents',                         Parent.objects.count()),
            ('Linked Parents',                  Parent.objects.filter(users__isnull=False).count()),
            ('Students',                        Student.objects.count()),
            ('Upcoming Sections',               Section.objects.filter(start_time__gt=datetime.now()).count()),
            ('Students in Upcoming Sections',   StudentSectionAssignment.objects.filter(status=SS_STATUS_ACCEPTED,
                                                    section__start_time__gt=datetime.now()).count()),
        )

        ssas = StudentSectionAssignment.objects.filter(status=SS_STATUS_APPLIED)\
            .order_by('applied_time').select_related('section', 'student', 'section__course')
        return render(request, 'app/admin.html', {
            'ssas':     ssas,
            'status':   status,
        })

    def post(self, request):
        if not request.user.is_staff:
            raise Http404

        if 'send-status-emails' in request.POST:
            status_template = get_template('app/email/status.html')
            dbsis_url = 'https://' + request.get_host() + reverse('index')

            connection = mail.get_connection()
            connection.open()
            msgs = []
            sections = Section.objects.filter(start_time__gt=datetime.now())
            news_items = NewsItem.objects.all().order_by('-updated')

            send_to_admin = 'send-to-admin' in request.POST
            send_only_wanted_upcoming = 'send-only-wanted-upcoming' in request.POST

            upcoming_course_ids = [s.course_id for s in sections]

            for parent in email_parents(
                    upcoming_course_ids,
                    send_to_admin and 'send-a-fraction' in request.POST,
                    'send-only-upcoming' in request.POST, send_only_wanted_upcoming,
                    ):
                user = parent.users.first()

                rows = SectionRows(sections, user)
                html_content = status_template.render(
                    {'user': user, 'parent': parent, 'dbsis_url': dbsis_url,
                        'section_rows': rows, 'show_students': True, 'show_status': True,
                        'show_internal_links': False, 'news_items': news_items, })
                text_content = html2text.html2text(html_content)

                msg = EmailMultiAlternatives('Status of Dave B’s Young Programmers', text_content,
                    'Dave B’s Student Information System <daveb@davebsoft.com>',
                    ['%s <%s>' % (parent.name, 'daveb@davebsoft.com' if send_to_admin else parent.email)])
                msg.attach_alternative(html_content, "text/html")
                msgs.append(msg)

            connection.send_messages(msgs)
            connection.close()

        return redirect(reverse('admin'))


def passthrough(parents):
    return filter(lambda _: True, parents)


def random_subset(parents):
    return filter(lambda _: random.random() < .05, parents)


def upcoming(parents):
    return filter(lambda parent: parent.has_upcoming, parents)


def upcoming_wanted(upcoming_course_ids):
    def upcoming_wanted_inner(parents):
        return filter(lambda parent: parent.has_student_wanting(upcoming_course_ids), parents)
    return upcoming_wanted_inner


def email_parents(upcoming_course_ids, send_a_fraction=False, send_only_upcoming=False, send_only_wanted_upcoming=False):
    f1 = random_subset                          if send_a_fraction              else passthrough
    f2 = upcoming                               if send_only_upcoming           else passthrough
    f3 = upcoming_wanted(upcoming_course_ids)   if send_only_wanted_upcoming    else passthrough

    return f1(f2(f3(Parent.objects.exclude(email__isnull=True).exclude(email__exact=''))))
