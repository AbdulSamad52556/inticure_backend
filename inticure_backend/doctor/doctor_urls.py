from django.urls import path, include

from .routers import router

from .views import appointment_close_view, appointment_list_view, appointment_status_update_view, appointment_detail_view, \
    appointment_schedule_view, observations_view, prescriptions_view, prescriptions_text_view, analysis_info_view, \
    order_escalate_view, doctor_specialization_view, order_accept_view, doctor_earnings_view, dashboard_view, \
    doctor_profile_view, senior_doctor_transfer_view, junior_doctor_transfer_view, available_slots_view, \
    create_followup_reminder_view, followup_reminder_list_view, create_discussion_view, discussion_list_view,\
    working_hour_view,working_hour_list_view,calender_view,timeslot_list_view,specialization_timeslot_view,\
    calender_edit_view,appointment_patient_history,calender_add_view,escalate_appointment_view, doctors_list_view, escalated_one, doctor_time_slots,appointment_completed, timeslots,\
    specialization_timeslot_view_reschedule, block_doctor, unblock_doctor, is_dr_blocked

urlpatterns = [
    path('appointment_list', appointment_list_view, name='appointment_list'),
    path('appointment_status_update', appointment_status_update_view, name='appointment_status_update'),
    path('appointment_detail', appointment_detail_view, name='appointment_detail'),
    path('appointment_schedule', appointment_schedule_view, name='appointment_schedule'),
    path('observations', observations_view, name='observations'),
    path('prescriptions', prescriptions_view, name='prescriptions'),
    path('prescriptions_text', prescriptions_text_view, name='prescriptions_text'),
    path('analysis_info', analysis_info_view, name='analysis_info'),
    path('order_escalate',order_escalate_view,name='order_escalate' ),
    path('escalate_appointment', escalate_appointment_view, name='escalate_appointment'),
    path('escalated_one', escalated_one, name='escalated_one'),
    path('doctor_list', doctors_list_view, name='doctor_list'),
    path('order_accept',order_accept_view,name='order_accept' ),
    path('doctor_specialization',doctor_specialization_view,name='doctor_specialization'),
    path('doctor_earnings',doctor_earnings_view,name='doctor_earnings'),
    path('doctor_dashboard',dashboard_view,name='doctor_dashboard'),
    path('doctor_profile',doctor_profile_view,name='doctor_profile'),
    path('senior_doctor_transfer',senior_doctor_transfer_view,name='senior_doctor_transfer'),
    path('junior_doctor_transfer',junior_doctor_transfer_view,name='junior_doctor_transfer'),
    path('available_slots',available_slots_view,name='available_slots'),
    path('create_followup_reminder',create_followup_reminder_view,name='create_followup_reminder'),
    path('followup_reminder_list',followup_reminder_list_view,name='followup_reminder_list'),
    path('create_discussion',create_discussion_view,name='create_discussion'),
    path('discussion_list',discussion_list_view,name='discussion_list'),
    path('working_hours',working_hour_view,name='working_hours'),
    path('working_hours_list',working_hour_list_view,name='working_hours_list'),
    path('calender_view',calender_view,name='calender_view'),
    path('time_slot_list',timeslot_list_view,name='time_slot_list'),
    path('specialization_time_slot',specialization_timeslot_view,name='specialization_time_slot'),
    path('specialization_time_slot_reschedule',specialization_timeslot_view_reschedule,name='specialization_time_slot_reschedule'),
    path('calender_edit',calender_edit_view,name='calender_edit'),
    path('calender_add',calender_add_view,name='calender_add'),
    path('appointment_close',appointment_close_view,name='appointment_close'),
    path('appointment_patient_history',appointment_patient_history,name='appointment_patient_history'),
    path('doctor_time_slots',doctor_time_slots,name='doctor_time_slots'),
    path('appointment_completed',appointment_completed,name='appointment_completed'),
    path('timeslots',timeslots,name='timeslots'),
    path('block_doctor/<int:doctor_id>/', block_doctor, name='block_doctor'),
    path('unblock_doctor/<int:doctor_id>/', unblock_doctor, name='unblock_doctor'),
    path('is_dr_blocked/', is_dr_blocked, name='is_dr_blocked'),
    path('', include(router.urls))
]
