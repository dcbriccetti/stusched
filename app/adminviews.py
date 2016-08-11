from datetime import datetime
from urllib.parse import urlencode
from django.core import mail
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import View
from django.core.mail import EmailMultiAlternatives
import html2text
from app.models import Parent, Student, Section, StudentSectionAssignment, SS_STATUS_APPLIED, SS_STATUS_ACCEPTED
from app.sections import SectionRows


class Admin(View):
    def get(self, request):
        class Status:
            def __init__(self):
                self.num_parents = Parent.objects.count()
                self.num_linked_parents = Parent.objects.filter(users__isnull=False).count()
                self.num_students = Student.objects.count()
                self.num_upcoming_sections = Section.objects.filter(start_time__gt=datetime.now()).count()
                self.num_accepted_upcoming = StudentSectionAssignment.objects.filter(status=SS_STATUS_ACCEPTED,
                    section__start_time__gt=datetime.now()).count()

        ssas = StudentSectionAssignment.objects.filter(status=SS_STATUS_APPLIED)\
            .order_by('applied_time').select_related('section', 'student', 'section__course')
        return render(request, 'app/admin.html', {
            'ssas':     ssas,
            'status':   Status(),
        })


class AdminEmail(View):
    def get(self, request):
        status_template = get_template('app/email/status.html')
        parents = Parent.objects.exclude(email__isnull=True).exclude(email__exact='')
        dbsis_url = 'https://dbsis.herokuapp.com'

        connection = mail.get_connection()
        connection.open()
        msgs = []
        sections = Section.objects.all()

        for parent in parents:
            user = parent.users.first()
            signup_url = dbsis_url + '/app/login?' + urlencode({
                'name':         parent.name,
                'email':        parent.email,
                'parent_code':  parent.code
            }) if parent.code and not user else None

            rows = SectionRows(sections, user)
            html_content = status_template.render({
                'parent':       parent,
                'dbsis_url':    dbsis_url,
                'signup_url':   signup_url,
                'section_rows': rows,
                'show_students': True,
                'show_internal_links': False,
            })
            text_content = html2text.html2text(html_content)

            msg = EmailMultiAlternatives('Status of Dave B’s Young Programmers', text_content,
                'Dave B’s Student Information System <daveb@davebsoft.com>', ['%s <%s>' % (parent.name, parent.email)])
            msg.attach_alternative(html_content, "text/html")
            msgs.append(msg)

        connection.send_messages(msgs)
        connection.close()

        return redirect(reverse('admin'))
