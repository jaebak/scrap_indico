Scripts to collect links from indico (described at [`collect_indico_links.py`](#collect_indico_links)) and write collected links to twiki (described at [`write_to_twiki.py`](#write_to_twiki)).

Requirements for `collect_indico_links.py`: python3, indico token (described at [indico token](#indico_token))  
Requirements for `write_to_twiki.py`: python3, `cern_sso.py` (described at [downloading cern sso](#cern_sso)), certificate and key to login to tiwki (described at [generating certificate and key](#cert_key))  
Required python libraries: `six`, `requests`

Example usage: 

`collect_indico_links.py --indico_token indp_xxxxxx --category_id 999 --event_titles "Inclusive weekly" "Leptonic weekly" --from_time=2021-01-01 --to_time today --output_directory jsons --indico_url https://indico.cern.ch`

`write_to_twiki.py --cert_filename xxx.pem --key_filename xxx.key --parent_topic YYY --output_twiki_url "https://twiki.cern.ch/twiki/bin/viewauth/PATH/TO_PAGE" --json_filenames jsons/meeting_inclusive_weekly.json jsons/meeting_leptonic_weekly.json --titles_for_jsons "Inclusive Meetings" "Leptonic Meetings"`

# <a name="collect_indico_links"></a>About `collect_indico_links.py`

Scraps indico using indico api and saves information into json files.

Script searches through an indico category for the each specified event title.  
For each event, each talk's tiles, presentors, and attachment links are scrapped.  
The scrapped information is saved into a `meeting_xxx.json` file, where there will be different files for each specified event title.  
If the `meeting_xxx.json` file exists, the newly scrapped information is combined into the file.  
Newly scrapped information will be chosen if there is an overlap in the existing `meeting_xxx.json` file.  

## Details:

### indico api
indico api reference can be found at https://indico.readthedocs.io/en/v1.9/http_api/access/

### <a name="indico_token"></a>indico token 
Indico api requires an indico token string (argument: `indico_token`).  
Make token string by going to indico's "My profile -> Settings -> API tokens" and pressing "Create new token".  
Check "Classic API (read only)" in Scopes and then "Save".  
The token string should be shown on the indico website.  
Example usage: `--indico_token indp_xxxxxx`  

### indico category id
The indico category id (argument: `category_id`) can be found by looking at the url of indico.  
Example: category id is 20 for the following URL: `https://indico.xxxx.xx/category/20`

### event title
The search for event titles (argument: `event_titles`) is done using regex, where uppercase and lowercase are ignored.  
Example regex usage: `--event_titles SUSY.*Weekly`

### start date and end date
The start date (argument: `from_time`) and end date (argument: `to_time`) to search for events in categories uses the format specified in "param from/to" in https://indico.readthedocs.io/en/v1.9/http_api/common/  
Example date formats: YYYY-MM-DD, -14d, today.  
Note when entering negative days as arugment use "=".  
Example usage: `--from_time=-14d`  

### output json file
The json filename will be from the specified event title which is slugified to a filename-friendly filename and made to undercase, with a prefix `meeting_`
Example: `--event_titles SUSY.*Weekly` will make a json file called `meeting_susy_weekly.json`

The json format is shown below, which is a list of event information  
`[ { 'date', 'url', 'title', 'presentations': [{'title', presenters:['presenter'], 'attachments': [('title', 'url')]}] } ]`

# <a name="write_to_twiki"></a>About `write_to_twiki.py`

Uses scrapped indico json files to write list of meetings and presentations to a target twiki page.  
The twiki page will have a list of meetings for each scrapped indico json file.  

## Details: 

### <a name="cern_sso"></a>Downloading `cern_sso.py`

`cern_sso.py` is used to login to twiki.  
Download `cern_sso.py` from https://github.com/cerndb/cern-sso-python with below command.  

`wget https://raw.githubusercontent.com/cerndb/cern-sso-python/master/cern_sso.py`

### <a name="cert_key"></a>Generating certificate and key for `cern_sso.py`

This script uses `cern_sso.py` (https://github.com/cerndb/cern-sso-python) to log into CERN twiki,  
where `cern_sso.py` requires a SSL certifiate and an unencrypted key for authentication.  
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

### Writing to twiki

To write to the twiki, https://twiki.cern.ch/twiki/bin/view/TWiki/TWikiScripts#save is used,  
where a http POST method is used.

### topic parent

Each twiki page has a topic parent (argument: `parent_topic`), where if set to 'none' there will be no parent topic.  
https://twiki.cern.ch/twiki/bin/view/TWiki/TWikiScripts#save has more information.

### output twiki page

The output twiki url (argument: `output_twiki_url`) is expected to have the following format,  
https://twiki.cern.ch/twiki/bin/view/PATH/TO_PAGE or https://twiki.cern.ch/twiki/bin/viewauth/PATH/TO_PAGE  
where to write to the twiki page, `view` or `viewauth` will be replaced with `save`.  

The twiki page will have a list of meetings for each scrapped indico json file.  
There will be a title (argument: `titles_for_jsons`) in the twiki page for each scrapped indico json file.  
Therefore the number of (argument: `json_filenames`) and (argument: `titles_for_jsons`) needs to be the same.
