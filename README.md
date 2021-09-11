Scripts to collect links from indico and write collected links to twiki.

Requirements: python3, indico token

# About `collect_indico_links.py`

Example usage: `collect_indico_links.py --indico_token indp_xxx --category_id 999 --event_titles "Inclusive meeting" "Leptonic meeting" --from_time=2021-01-01 --to_time today --output_directory jsons --indico_url https://indico.cern.ch`

Scraps indico using indico api and saves information into json files.

Script searches through an indico category for the each specified event title.  
For each event, each talk's tiles, presentors, and attachment links are scrapped.  
The scrapped information is saved into a `meeting_xxx.json` file, where there will be different files for each specified event title.  
If the `meeting_xxx.json` file exists, the newly scrapped information is combined into the file.  
Newly scrapped information will be chosen if there is an overlap in the existing `meeting_xxx.json` file.  

## Details:

indico api reference can be found at https://indico.readthedocs.io/en/v1.9/http_api/access/

Indico api requires an indico token string (argument: `indico_token`).  
Make token string by going to indico's "My profile -> Settings -> API tokens" and pressing "Create new token".  
Check "Classic API (read only)" in Scopes and then "Save".  
The token string should be shown on the indico website.  
Example usage: `--indico_token indp_xxxxxx`  

The indico category id (argument: `category_id`) can be found by looking at the url of indico.  
Example: category id is 20 for the following URL: `https://indico.xxxx.xx/category/20`

The search for event titles (argument: `event_titles`) is done using regex, where uppercase and lowercase are ignored.  
Example regex usage: `--event_titles SUSY.*Meeting`

The start date (argument: `from_time`) and end date (argument: `to_time`) to search for events in categories uses the format specified in "param from/to" in https://indico.readthedocs.io/en/v1.9/http_api/common/  
Example date formats: YYYY-MM-DD, -14d, today.  
Note when entering negative days as arugment use "=".  
Example usage: `--from_time=-14d`  

The json filename will be from the specified event title which slugified to a filename-friendly filename.

The json format is shown below, which is a list of event information  
`[ { 'date', 'url', 'title', 'presentations': [{'title', presenters:['presenter'], 'attachments': [('title', 'url')]}] } ]`
