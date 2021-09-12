#!/usr/bin/env python3

"""
Description: Using scrapped indico json files, writes meetings to a target twiki page.
   Code URL: https://github.com/jaebak/scrap_indico
     Author: Jaebak Kim
    Contact: fusionhep@gmail.com
       Date: 2021.09.13
"""
import requests
import cern_sso
import json
import argparse
import sys

def by_date(meeting):
  return meeting['date']

def add_meeting(title, meetings_filename, text):
  # Get meeting file
  # meetings = [{'date', 'url', 'title'(meeting), 'presentations':[{'title'(presentation), presenters:['presenter'], 'attachments': [('title', 'url')]}]}]
  with open(meetings_filename) as json_file:
    meetings = json.load(json_file)
  meetings.sort(key=by_date, reverse=True)
  #print(meetings)

  text += '---++ '+title+'\n'
  for meeting in meetings:
    if 'title' in meeting:
      text += '---+++!! ['+meeting['date']+'] [['+meeting['url']+']['+meeting['title']+']]\n'
    else:
      text += '---+++!! [['+meeting['url']+']['+meeting['date']+']]\n'
    # One line per presentation
    for presentation in meeting['presentations']:
      text += '   * '+presentation['title']+': '
      text += ', '.join(presentation['presenters'])+': ('
      attachment_text = ''
      for attachment in presentation['attachments']:
        if attachment_text != '': attachment_text += ', '
        attachment_text += '[['+attachment[1]+']['+attachment[0]+']]'
      text += attachment_text+')\n'
  return text

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='''\
Using scrapped indico json files, writes meetings to a target twiki page.

Example command: 

Details: 

This script uses `cern_sso.py` (https://github.com/cerndb/cern-sso-python) to log into CERN twiki,
where cern_sso.py requires a SSL certifiate and an unencrypted key for authentication.
`cern_sso.py` creates a cookie that this script uses to write content into the twiki.

The following steps generates a certificate and an unencrypted key from a `xxx.p12` certificate.
Note, `xxx.p12` is normally located in `~/.globus`.
Note, because the key is unencrypted, please make sure that the files are in a secure location!
1. Generate a certificate from `xxx.p12`
`openssl pkcs12 -clcerts -nokeys -in xxx.p12 -out myCert.pem`
2. Make a separate encrypted key file for the key inside `xxx.p12`
`openssl pkcs12 -nocerts -in xxx.p12 -out myCert.tmp.key`
3. Create an unencrypted key from `myCert.tmp.key`
`openssl rsa -in myCert.tmp.key -out myCert.key`

To write to the twiki, https://twiki.cern.ch/twiki/bin/view/TWiki/TWikiScripts#save is used,
where a http POST method is used.

Each twiki page has a topic parent, where if set to 'none' there will be no parent topic.

The output twiki url is expected to have the following format,
https://twiki.cern.ch/twiki/bin/view/PATH/TO_PAGE or https://twiki.cern.ch/twiki/bin/viewauth/PATH/TO_PAGE
where to write to the twiki page, `view` or `viewauth` will be replaced with `save`.

The twiki page will have a list of meetings for each scrapped indico json file.
There will be a title (argument: titles_for_jsons) in the twiki page for each scrapped indico json file.
Therefore the number of (argument: json_filenames) and (argument: titles_for_jsons) needs to be the same.
''', formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-c','--cert_filename', required=True, help='Certificate filename used to log into CERN twiki')
  parser.add_argument('-k','--key_filename', required=True, help='Key filename used to log into CERN twiki')
  parser.add_argument('-p','--parent_topic', required=True, help="Parent topic to be used for output twiki page. Set to 'none' if no parent topic is needed.")
  parser.add_argument('-o','--output_twiki_url', required=True, help='Twiki url to write content, where url should include view or viewauth')
  parser.add_argument('-j', '--json_filenames', required=True, nargs="+", help="Scrapped indico JSON filenames")
  parser.add_argument('-t', '--titles_for_jsons', required=True, nargs="+", help="Titles to put in twiki for each scrapped indico JSON file")

  args = parser.parse_args()

  if len(args.json_filenames) != len(args.titles_for_jsons):
    print('[Error] Argument json_filenames and argument titles_for_jsons does not have the same number of arguments.')
    sys.exit()

  cert_file = args.cert_filename
  key_file = args.key_filename

  view_url = args.output_twiki_url
  target_url = args.output_twiki_url.replace('viewauth','save').replace('view','save')
  login_url = '/'.join(args.output_twiki_url.split('/')[:-1])

  print("The following URLs will be used")
  print("   Login URL: "+login_url)
  print("    Save URL: "+target_url)
  print("  Output URL: "+view_url)
  print()

  parent = args.parent_topic
  
  json_filenames = args.json_filenames
  titles = args.titles_for_jsons

  # Make text for twiki
  text = 'On this page:<br>%TOC%\n'
  for ijson, meetings_filename in enumerate(json_filenames):
    target_title = titles[ijson]
    text = add_meeting(target_title, meetings_filename, text)

  # Write text to twiki
  print('Getting cookies using cern_sso')
  cookies = cern_sso.cert_sign_on(login_url, cert_file=cert_file, key_file=key_file, cookiejar=None)
  print('Writing to twiki with URL: '+target_url)
  form = {'text':text,
          'topicparent': parent,
          'forcenewrevision': '1'}
  r1 = requests.post(target_url, data=form, cookies=cookies)
  print('Content was written to '+view_url)
