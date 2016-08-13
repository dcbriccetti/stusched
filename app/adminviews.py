import logging
import random
from datetime import datetime
from urllib.parse import urlencode
from django.core import mail
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import View
from django.core.mail import EmailMultiAlternatives
import html2text
from app.models import Parent, Student, Section, StudentSectionAssignment, SS_STATUS_APPLIED, SS_STATUS_ACCEPTED, \
    NewsItem
from app.sections import SectionRows

log = logging.getLogger(__name__)


class Admin(View):
    def get(self, request):
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
        if 'send-status-emails' in request.POST:
            status_template = get_template('app/email/status.html')
            parents = Parent.objects.exclude(email__isnull=True).exclude(email__exact='')
            dbsis_url = 'https://dbsis.herokuapp.com'

            connection = mail.get_connection()
            connection.open()
            msgs = []
            sections = Section.objects.filter(start_time__gt=datetime.now())
            send_to_admin = 'send-to-admin' in request.POST
            send_a_fraction = send_to_admin and 'send-a-fraction' in request.POST
            send_only_upcoming = 'send-only-upcoming' in request.POST
            news_items = NewsItem.objects.all().order_by('-updated')

            for parent in parents:
                if (not send_only_upcoming or parent.has_upcoming) and (not send_a_fraction or random.random() < .15):
                    user = parent.users.first()
                    signup_url = dbsis_url + '/app/login?' + urlencode({
                        'name':         parent.name,
                        'email':        parent.email,
                        'parent_code':  parent.code
                    }) if parent.code and not user else None

                    rows = SectionRows(sections, user)
                    html_content = status_template.render({
                        'user':         user,
                        'parent':       parent,
                        'dbsis_url':    dbsis_url,
                        'signup_url':   signup_url,
                        'section_rows': rows,
                        'show_students': True,
                        'show_status':  True,
                        'show_internal_links': False,
                        'news_items':   news_items,
                    })
                    text_content = html2text.html2text(html_content)

                    msg = EmailMultiAlternatives('Status of Dave B’s Young Programmers', text_content,
                        'Dave B’s Student Information System <daveb@davebsoft.com>', ['%s <%s>' %
                        (parent.name, 'daveb@davebsoft.com' if send_to_admin else parent.email)])
                    msg.attach_alternative(html_content, "text/html")
                    msgs.append(msg)

            connection.send_messages(msgs)
            connection.close()

        return redirect(reverse('admin'))
