from __future__ import print_function

import datetime
import os.path
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_DIR = Path(__file__).resolve().parent.parent


def generate_google_meet(summary, description, attendees, start_time, end_time):
    print("generate meet link functtion")
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    try:
        print("meeting link try block")
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        print("creds",None)
        if os.path.exists(str(os.path.join(BASE_DIR, 'conf_files/token.json'))):
            print("inside meeting link if loop")
            creds = Credentials.from_authorized_user_file(str(os.path.join(BASE_DIR, 'conf_files/token.json')), SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            print("checking if creds is valid")
            if creds and creds.expired and creds.refresh_token:
                print("refreash creds")
                creds.refresh(Request())
                print("refreshed")
            else:
                print("else creds ")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(os.path.join(BASE_DIR, 'conf_files/client_secret.json'))
                    , SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            print("otuside creds refreash")
            with open(str(os.path.join(BASE_DIR, 'conf_files/token.json')), 'w') as token:
                token.write(creds.to_json())
    except Exception as e:
        print("meeting link exception block")
        print("exception meeting link",e)
        return 0
    try:
        print("start_time",start_time)
        print("end_time",end_time)
        time_data = start_time
        try:
            start_time = time_data + ':00'
        except ValueError as e:
            print(f"Error: {e}")
        # start_time= datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") 
        print("attendees",attendees)
        service = build('calendar', 'v3', credentials=creds)
        event = {
            "conferenceDataVersion": 1,
            'summary': summary,
            # 'location': '800 Howard St., San Francisco, CA 94103',
            'description': description,
            'start': {
                # 'dateTime': '2022-10-26T20:25:00-07:00',
                'dateTime': start_time,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Kolkata',
            },
            # 'recurrence': [
            #     'RRULE:FREQ=DAILY;COUNT=2'
            # ],
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    },
                    "requestId": "RandomString",
                }
            },
            'visibility': 'public',
            "anyoneCanAddSelf":True,
            'attendees': attendees,
            'reminders': {

                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        print("insert")
        event = service.events().insert(calendarId='primary', conferenceDataVersion=1, body=event).execute()
        print(event)
        print('Event created: %s' % (event.get('htmlLink')))
        return event.get('hangoutLink')
        
    except HttpError as error:
        print('An error occurred: %s' % error)
        return 0
# generate_google_meet("Inticure,Preliminary Analysis","",[{"email":"arunraj0861@gmail.com"},{"email":"abhirampblm11@gmail.com"}],'2022-10-28T20:25:00-07:00','2022-10-28T20:25:00-07:00')# start_time_time_slots = "1PM-12AM"
# # time_slots = Timeslots.objects.get(id=slot_id)
# start_time = start_time_time_slots.split('-')[0].strip()
# end_time = start_time_time_slots.split('-')[1].strip()
# print(datetime.datetime.strptime(start_time,'%I%p').time())
# print(datetime.datetime.strptime(start_time,'%I%p').time())

# if __name__ == '__main__':
#     main()
# event = {
#   'summary': 'Google I/O 2015',
#   'location': '800 Howard St., San Francisco, CA 94103',
#   'description': 'A chance to hear more about Google\'s developer products.',
#   'start': {
#     'dateTime': '2023-05-28T09:00:00-07:00',
#     'timeZone': 'America/Los_Angeles',
#   },
#   'end': {
#     'dateTime': '2023-05-28T17:00:00-07:00',
#     'timeZone': 'America/Los_Angeles',
#   },
#   'recurrence': [
#     'RRULE:FREQ=DAILY;COUNT=2'
#   ],
#   'attendees': [
#     {'email': 'arunraj0861@gmail.com'},
#   ],
#   'reminders': {
#     'useDefault': False,
#     'overrides': [
#       {'method': 'email', 'minutes': 24 * 60},
#       {'method': 'popup', 'minutes': 10},
#     ],
#   },
# }
#
# event = service.events().insert(calendarId='primary', body=event).execute()
# print( 'Event created: %s' % (event.get('htmlLink')))
