from requests_html import HTMLSession
import re
import requests
import urllib
import logging
import json
import os
import time

# Configs
logging.basicConfig(level=logging.INFO)
storage_root = "\\\\tower\Lego\\"
brickset_export = 'https://brickset.com/exportscripts/instructions'
lego_uri = "https://www.lego.com/en-us/service/buildinginstructions/"

# Pull from your cookies on lego.com
UAID = ""

# Special Characters [:, ", /, ™, ®, "?"]
special_chars = [u"\u003A", u"\u0022", "/", u"\u2122", u"\u00AE", "?"]

# List of previously checked set_ids
existing_list = []
temp_list = []

# Get all sets from Brinkset
response = requests.get(brickset_export)

# Break giant block of text into list
response_list = response.text.split('\n')
response_list.pop(0)

# Attempt to open previously downloaded sets file
try:
    f = open ('{}saved_sets.json'.format(storage_root), 'r')
    existing_list = json.load(f)
    f.close()
except IOError:
    f = open ('{}saved_sets.json'.format(storage_root), 'w')
    json.dump(existing_list, f)
    f.close()

# Lets download some files
session = HTMLSession()
for i in range(len(response_list)):
    # Get clean set number from brickset
    current_set = re.search('"(\d*)-\d"', response_list[i])

    if current_set is not None:
        current_set_clean = current_set.group(1)

        # Lego is missing some names, fallback to brickset
        try:
            backup_name = re.search('(?<=pdf",")(.*?)(?=",")', response_list[i]).group(1)
            clean_backup_name = re.sub('^\d* ', '', backup_name)
        except:
            continue

        # Check list to make sure we haven't downloaded before
        if current_set_clean not in existing_list and current_set_clean not in temp_list:
            # Requests_HTMl seems to have an issue after a bunch of requests
            # so we'll refresh it every so often
            if i % 15 == 0:
                session.close()
                session = HTMLSession()

            web_response = session.get(lego_uri + current_set_clean, timeout=15)
            web_response.html.render(sleep=.5, timeout=15)

            # Get name, theme and release year from page
            set_id = current_set_clean
            logging.debug("{}".format(set_id))
            try:
                raw_name = web_response.html.find('h1', first=True).text
            except:
                # Skip check just for this run. Check again on future runs (prevents newly added sets from being skipped)
                logging.warning("Set was not found on Lego.com: {}".format(set_id))
                temp_list.append(current_set_clean)
                continue

            try:
                set_name = raw_name.split(', ')[1]
            except:
                set_name = clean_backup_name
                logging.info("Issue with set name on set, using backup: {} - {}".format(set_id, set_name))

            try:
                set_theme = raw_name.split(', ')[2]
            except:
                set_theme = "Unknown"

            try:
                raw_year = web_response.html.find('.c-content', first=True).text
                set_year = re.search('\d{4}', raw_year).group(0)
            except:
                logging.warning("Issue with year, will try again later: {}".format(set_id))
                temp_list.append(current_set_clean)
                continue

            #Remove special characters from name
            for ch in special_chars:
                set_name = set_name.replace(ch, "")
                set_theme = set_theme.replace(ch, "")

            # Get instruction links
            wanted_instructions = []
            booklets = web_response.html.find('.c-bi-booklet', first=True).links

            if not booklets:
                logging.warning("No instructions found for set, will try again later: {}".format(set_id))
                temp_list.append(current_set_clean)
                continue

            for booklet_link in booklets:
                # Check to see if link is one we want
                if re.search('\w.pdf', booklet_link):
                    wanted_instructions.append(booklet_link)
            
            # Get set image
            grid_item = web_response.html.find('.c-card__img')
            if len(grid_item) == 1:
                set_image = re.search('https:.*(jpg|JPG|png|PNG)', grid_item[0].html).group(0)
            else:
                set_image = re.search('https:.*(jpg|JPG|png|PNG)', grid_item[1].html).group(0)

            # Pretty up file name and path
            formatted_set_name = "{} - {} ({})".format(set_id, set_name, set_year)
            set_directory = "{}{}/{}".format(storage_root, set_theme, formatted_set_name)

            # Check download path, if it exists skip download
            if not os.path.isdir(set_directory):
                logging.info("Downloading data for {}".format(set_id))
                os.makedirs(set_directory)

                # Download items from LEGO site
                # Grab all wanted instruction books
                for i in range(len(wanted_instructions)):
                    try:
                        opener = urllib.request.build_opener()
                        opener.addheaders = [('Cookie',"UAID={}".format(UAID))]
                        urllib.request.install_opener(opener)
                        urllib.request.urlretrieve(wanted_instructions[i], "{}/{}-#{}{}".format(set_directory, formatted_set_name, i+1, ".pdf"))
                    except Exception as ex:
                        logging.warning("Problem downloading books for {}".format(set_id))
                        continue
                try:
                    urllib.request.urlretrieve(set_image, "{}/{}{}".format(set_directory, formatted_set_name, ".jpg"))
                except:
                    logging.warning("Problem downloading image for {}".format(set_id))
                    continue
            else:
                logging.debug("Skipping - file path aleady already exists for set: {}".format(set_id))

            existing_list.append(current_set_clean)
        else:
            logging.debug("Previously downloaded {}".format(current_set_clean))

if existing_list:
    f = open ('{}saved_sets.json'.format(storage_root), 'w')
    json.dump(existing_list, f)
    f.close()
    
