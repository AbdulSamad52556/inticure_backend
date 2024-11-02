from django_cron import CronJobBase, Schedule
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from analysis.models import AppointmentHeader
from doctor.serializer import AppointmentHeaderSerializer
import datetime
from doctor.views import get_users_name,get_doctor_specialization,get_user_mail
from analysis.views import get_doctor_bio

class SendEmails(CronJobBase):
    RUN_EVERY_MINS = 1440 # run every 24 hours
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'common.send_reminder_email'    # a unique code for your job

    def do(self):
        tomorrow=datetime.date.today() + datetime.timedelta(days=1)
        appointments = AppointmentHeaderSerializer(AppointmentHeader.objects.filter(appointment_date=tomorrow),many=True).data
        print("appointmets",appointments)
        for appointment in appointments:
            weekday=(datetime.datetime.strptime(str(appointment['appointment_date']),"%Y-%m-%d")).strftime("%A")
            if appointment['is_free'] == 1 :
                subject = 'Don’t forget your upcoming FREE consultation'
                to_email = get_user_mail(appointment['user_id'])
                context = {'date':appointment['appointment_date'],'time':appointment['appointment_time_slot_id'],'c_name':get_users_name(appointment['user_id']),\
                "weekday":weekday,"specialization":get_doctor_specialization(appointment['senior_doctor']),\
                    'd_name':get_users_name(appointment['junior_doctor']),'doctor_flag':0,"subject":subject,"meeting_link":appointment['meeting_link']}
            else:
                subject = 'Reminder Appointment confirmation'
                to_email = get_user_mail(appointment['user_id'])
                doctor_bio,profile_pic=get_doctor_bio(appointment['senior_doctor'])
                context = {'date':appointment['appointment_date'],'time':appointment['appointment_time_slot_id'],'d_name':get_users_name(appointment['senior_doctor']),\
                "weekday":weekday,"specialization":get_doctor_specialization(appointment['senior_doctor']),'c_name':get_users_name(appointment['user_id']),\
                    "doctor_flag":1,"subject":subject,"meeting_link":appointment['senior_meeting_link'],
                    "doctor_bio":doctor_bio,"profile_pic":profile_pic}                
            from_email = 'Inticure <hello@inticure.com>'
            html_content = render_to_string('customer_reminder.html', context)
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
