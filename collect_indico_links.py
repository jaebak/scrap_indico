#!/usr/bin/env python3

"""
Description: Scraps indico using indico api and saves information into json files.
   Code URL: https://github.com/jaebak/scrap_indico
     Author: Jaebak Kim
    Contact: fusionhep@gmail.com
       Date: 2021.09.13
"""

import requests
import json
import os
import sys
import datetime
import argparse
import unicodedata
import re

def get_event_json(event_id, token):
  url = indico_url+'/export/timetable/'+str(event_id)+'.json'
  response = requests.get(url, headers={'Authorization': 'Bearer '+token})
  return response.json()

def get_presentations(timetable_json, presentations):
  if not type(timetable_json) is dict:
    return
  if 'startDate' in timetable_json:
    presentations.append(timetable_json)
    return
  else:
    for key in timetable_json:
      get_presentations(timetable_json[key], presentations)
    
def get_category_json(category_id, token, from_time='-7d', to_time='today', tz='Europe/Zurich'):
  url = indico_url+'/export/categ/'+str(category_id)+'.json?from='+from_time+'&to='+to_time+'&tz='+tz
  #print(url)
  response = requests.get(url, headers={'Authorization': 'Bearer '+token})
  return response.json()

def get_events(category_json, events):
  events.extend(category_json['results'])

def collect_events(events, title):
  collected_events = []
  for event in events:
    if title.lower() in event['title'].lower():
      collected_events.append(event)
  return collected_events

def collect_events_with_regex(events, title):
  collected_events = []
  for event in events:
    if re.search(title.lower(), event['title'].lower()):
      collected_events.append(event)
  return collected_events

# attachments = [{'title', 'download_url'}]
def get_attachments(presentation):
  if presentation['attachments']['files'] == None:
    return []
  return presentation['attachments']['files']

def get_presenters_string(presentation):
  if 'presenters' not in presentation: return 'no-name'
  presenter_string = ''
  for presenter in presentation['presenters']:
    if presenter_string != '': presenter_string += ', '
    presenter_string += presenter['name']
  return presenter_string

def get_presenter_list(presentation):
  if 'presenters' not in presentation: return ['no-name']
  presenters = []
  for presenter in presentation['presenters']:
    presenters.append(presenter['name'])
  return presenters

def get_attachment_string(presentation):
  if presentation['attachments']['files'] == None:
    return 'None'
  attachment_string = ''
  for attachment in presentation['attachments']['files']:
    if attachment_string != '': attachment_string += ', '
    attachment_string += attachment['title']+' ['+indico_url+attachment['download_url']+']'
  return attachment_string

# returns [(title, url)]
def get_attachment_list(presentation):
  if presentation['attachments']['files'] == None:
    return []
  attachments = []
  for attachment in presentation['attachments']['files']:
    attachments.append([attachment['title'],indico_url+attachment['download_url']])
  return attachments

def print_events(events):
  for event in events:
    print(event['startDate']['date']+' id='+event['id']+' title: '+event['title'])

def print_presentations(presentation):
  for presentation in presentations:
    if len(get_attachments(presentation)) == 0: continue
    print('Title: '+presentation['title'])
    print('  presenters:'+get_presenters_string(presentation))
    print('  attachments: '+get_attachment_string(presentation))

def url_is_in_meetings_result(meetings_result, url):
 for meeting_result in meetings_result:
   if url == meeting_result['url']: return True
 return False

# meetings_result = [{'date', 'url', [{'title', presenters:['presenter'], 'attachments': [('title', 'url')]}]}]
def merge_meeting_results(new, old):
  merged_meetings_results = new
  # Add in old, if not in new
  for meeting_result in old:
    url_old = meeting_result['url']
    if url_is_in_meetings_result(merged_meetings_results, url_old): continue
    merged_meetings_results.append(meeting_result)
  return merged_meetings_results

def by_datetime(presentation):
  date = presentation['startDate']['date']
  time = presentation['startDate']['time']
  return datetime.datetime.strptime(date+' '+time, '%Y-%m-%d %H:%M:%S')

def slugify(value, allow_unicode=False):
  """
  Taken from https://github.com/django/django/blob/master/django/utils/text.py
  Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
  dashes to single dashes. Remove characters that aren't alphanumerics,
  underscores, or hyphens. Convert to lowercase. Also strip leading and
  trailing whitespace, dashes, and underscores.
  """
  value = str(value)
  if allow_unicode:
      value = unicodedata.normalize('NFKC', value)
  else:
      value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
  value = re.sub(r'[^\w\s-]', '', value.lower())
  return re.sub(r'[-\s]+', '-', value).strip('-_')

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='''\
Scraps indico using indico api and saves information into json files.

Script searches through an indico category for the each specified event title. 
For each event, each talk's tiles, presentors, and attachment links are scrapped.
The scrapped information is saved into a meeting_xxx.json file, where there will be different files for each specified event title.
If the meeting_xxx.json file exists, the newly scrapped information is combined into the file.
Newly scrapped information will be chosen if there is an overlap in the existing meeting_xxx.json file.

Example command: collect_indico_links.py --indico_token indp_xxxxxx --category_id 999 --event_titles "Inclusive meeting" "Leptonic meeting" --from_time=2021-01-01 --to_time today --output_directory jsons --indico_url https://indico.cern.ch

Details:

indico api reference can be found at https://indico.readthedocs.io/en/v1.9/http_api/access/

Indico api requires an indico token string (argument: indico_token). 
Make token string by going to indico's "My profile -> Settings -> API tokens" and pressing "Create new token".
Check "Classic API (read only)" in Scopes and then "Save".
The token string should be shown on the indico website.
Example usage: --indico_token indp_xxxxxx

The indico category id (argument: category_id) can be found by looking at the url of indico.
Example: category id is 20 for the following URL: indico.xxxx.xx/category/20 

The search for event titles (argument: event_titles) is done using regex, where uppercase and lowercase are ignored.
Example regex usage: --event_titles SUSY.*Meeting

The start date (argument: from_time) and end date (argument: to_time) to search for events in categories uses the format specified in "param from/to" in https://indico.readthedocs.io/en/v1.9/http_api/common/
Example date formats: YYYY-MM-DD, -14d, today.
Note when entering negative days as arugment use "=". 
Example usage: --from_time=-14d

The json filename will be from the specified event title which slugified to a filename-friendly filename.

The json format is shown below, which is a list of event information
[ { 'date', 'url', 'title', 'presentations': [{'title', presenters:['presenter'], 'attachments': [('title', 'url')]}] } ]
''', formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-k', '--indico_token', required=True, help="Indico's token string")
  parser.add_argument('-c', '--category_id', required=True, help="Indico's category id. Events in the category will be search.")
  parser.add_argument('-e', '--event_titles', required=True, nargs="+", help="Event's title to be search for using regex")
  parser.add_argument('-o', '--output_directory', required=True, help="Output directory for json files")
  parser.add_argument('-u', '--indico_url', default='https://indico.cern.ch', help="URL for indico. Default is https://indico.cern.ch")
  parser.add_argument('-f', '--from_time', default="-30d", help="Event search start date. Default is -30d.")
  parser.add_argument('-t', '--to_time', default="today", help="Event search end date. Default is today.")
  args = parser.parse_args()

  # Setting
  token = args.indico_token

  category_id = args.category_id
  target_titles = args.event_titles
  from_time = args.from_time
  to_time = args.to_time
  data_folder = args.output_directory
  indico_url = args.indico_url

  if not os.path.exists(data_folder):
    os.makedirs(data_folder)

  # Get category from indico
  print('Getting information for category '+str(category_id)+"\n")
  category_json = get_category_json(category_id=category_id, token=token, from_time=from_time, to_time=to_time)

  for target_title in target_titles:
    # Organize category result
    #events = [{title, id, startDate, ...}]
    events = []
    get_events(category_json, events)
    #print_events(events)
    target_events = collect_events_with_regex(events, target_title)
    #print(target_events)
    print("Searching for: "+target_title)
    if len(target_events) != 0:
      print("Following events are found")
      print_events(target_events)
    else:
      print("No events are found")

    # Collect information from event
    meetings_result_filename = data_folder+'/'+slugify('meeting_'+target_title.replace(' ','_').replace('/','_'))+'.json'
    # meetings_result = [{'date', 'url', 'title'(for event), 'presentations': [{'title'(for presentation), presenters:['presenter'], 'attachments': [('title', 'url')]}]}]
    meetings_result = []
    for event in target_events:
      print('Getting information for "'+event['title']+'" with event id: '+event['id']+' date: '+event['startDate']['date'])
      # Get timetable from indico
      event_id = event['id']
      timetable_json = get_event_json(event_id=event_id, token=token)  

      # Organize timetable result
      # presentations = [{attachments, presenters, url, ...}]
      presentations = []
      get_presentations(timetable_json, presentations)
      presentations.sort(key=by_datetime)
      #print(presentations)
      #print_presentations(presentations)

      # meeting_result = {'date', 'url', 'title'(meeting), 'presentations': [{'title'(presentation), presenters:['presenter'], 'attachments': [('title', 'url')]}]}
      meeting_result = {}
      meeting_result['date'] = event['startDate']['date']
      meeting_result['url'] = event['url']
      meeting_result['title'] = event['title']
      meeting_result['presentations'] = []
      for presentation in presentations:
        # presentation_result = {'title', presenters:['presenter'], 'attachments': [('title', 'url')]}
        presentation_result = {}
        attachement_list = get_attachment_list(presentation)
        if len(attachement_list) == 0: continue
        presentation_result['title'] = presentation['title']
        presentation_result['presenters'] = get_presenter_list(presentation)
        presentation_result['attachments'] = attachement_list
        meeting_result['presentations'].append(presentation_result)
      if len(meeting_result['presentations']) != 0:
        meetings_result.append(meeting_result)
    #print(meetings_result)

    # Merge meeting_results
    if os.path.exists(meetings_result_filename):
      with open(meetings_result_filename) as json_file:
        meetings_result_disk = json.load(json_file)
      meetings_result = merge_meeting_results(new=meetings_result, old=meetings_result_disk)

    #print(meetings_result)
    if len(meetings_result) != 0:
      with open(meetings_result_filename, 'w') as json_file:
        json.dump(meetings_result, json_file, indent=2)
        print("Saved information into "+meetings_result_filename)

    print()
