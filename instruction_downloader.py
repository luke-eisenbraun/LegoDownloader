import json
import requests
import os
import re
import urllib
import simplejson
import logging

# Configs
logging.basicConfig(level=logging.INFO)
storage_root = "/mnt/user/Lego/"
brickset_export = 'https://brickset.com/exportscripts/instructions'
lego_api = "https://www.lego.com//service/biservice/search?fromIndex=0&locale=en-US&onlyAlternatives=false&prefixText="
# [:, ", /, ™, ®]
special_chars = [u"\u003A", u"\u0022", "/", u"\u2122", u"\u00AE"]

existing_list = []

# Get all sets from Brinkset
response = requests.get(brickset_export)

# Break giant block of text into list
response_list = response.text.split('\n')
# Remove header
response_list.pop(0)

# Attempt to open previously downloaded sets file
try:
    f = open ('saved_sets.json', 'r')
    existing_list = simplejson.load(f)
    f.close()
except IOError:
    f = open ('saved_sets.json', 'w')

# Loop through all sets
for i in range(len(response_list)):
    multiple_books = False

    # Get clean set number from brickset
    current_set = re.search('"(\d*)-\d"', response_list[i])
    current_set_clean = current_set.group(1)

    # Check list to make sure we haven't downloaded before
    if current_set_clean not in existing_list:
        response = requests.get(lego_api + current_set_clean)
        raw_data = json.loads(response.text)

        # Some listings contain multiple sets
        for product in range(len(raw_data["products"])):
            set_data = raw_data["products"][product]

            # Set information
            set_id = set_data["productId"]
            set_name = set_data["productName"]
            set_theme = set_data["themeName"]
            set_year = set_data["launchYear"] 
            set_image = set_data["buildingInstructions"][0]["frontpageInfo"]

            instruction_list = {}
            instructions = set_data["buildingInstructions"]
            
            # Remove special characters from name
            for ch in special_chars:
                set_name = set_name.replace(ch, "")
                set_theme = set_theme.replace(ch, "")

            # Check to see if there are multiple versions/books for set
            if len(instructions) > 1 and bool(re.search('(\s1/|BOOK \d( |$))', instructions[0]['description'])):
                try:
                    version = re.search('[vV](er)?(ER)?[sS]?.? ?\d\d', instructions[0]['description']).group(0)
                except:
                    # No version format in description
                    version = ""
                wanted_version_locs = []

                # Find the location of same version books
                for k in range(len(instructions)):
                    if version in instructions[k]["description"]:
                        wanted_version_locs.append(k)
                
                # Parse book # from matching version descriptions
                for item in wanted_version_locs:
                    try:
                        # LEGO has some stupid naming conventions
                        book_match = re.search('( 1?\d/\d{1,2}(\s|$)|BOOK \d( |$)| BOG\d)', instructions[item]["description"])
                        book_total = book_match.group(0).replace(" ", "").replace("BOOK", "").replace("BOG", "")
                        book = book_total.split('/')[0]
                        instruction_list[instructions[item]["pdfLocation"]] = book
                    except:
                        logging.warning("Couldn't parse description for book")

                logging.debug("Downloading multiple books for: {}".format(set_id))
            else:
                instruction_list[instructions[0]["pdfLocation"]] = "1"

            if set_theme is None:
                logging.debug("Setting theme to Random")
                set_theme = "Random"

            formatted_set_name = "{} - {} ({})".format(set_id, set_name, set_year)
            set_directory = "{}{}/{}".format(storage_root, set_theme, formatted_set_name)

            # Check download path, if it exists skip download
            if not os.path.isdir(set_directory):
                logging.info("Downloading data for {}".format(set_id))
                os.makedirs(set_directory)

                # Download items from LEGO site
                # Grab all wanted instruction books
                for url in instruction_list:
                    try:
                        urllib.request.urlretrieve(url, "{}/{}-#{}{}".format(set_directory, formatted_set_name, instruction_list[url], ".pdf"))
                    except:
                        logging.warning("Problem downloading books for {}".format(set_id))
                        continue

                try:
                    urllib.request.urlretrieve(set_image, "{}/{}{}".format(set_directory, formatted_set_name, ".png"))
                except:
                    logging.warning("Problem downloading image for {}".format(set_id))
                    continue
            else:
                logging.info("Skipping - file path aleady already exists for set: {}".format(set_id))
            
            existing_list.append(set_id)
    else:
        logging.info("Previously downloaded {}".format(current_set_clean))

if existing_list:
    f = open ('saved_sets.txt', 'w')
    simplejson.dump(existing_list, f)
    f.close()
