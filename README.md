# Airtable Import
A program designed to take PDFs and extract data for upload to Airtable. Files are available to build a Docker container.
### To Run:
The program can be run directly, so long as you have Python installed and install any dependencies by running this command from the command line: `pip install pywin32, requests, pypdf2`.
Otherwise, it can be run from Docker by running the following commands from within the program's folder:
```
docker image build -t airtable .

docker run --name airtable --rm airtable
```
The first line will build the docker container image from the files in the current working directory according to the instructions in the Dockerfile. It will name the image `airtable`.
The second line will run the container after it has been built. The running container will be named `airtable` and will be automatically removed if the container stops. If you need to stop the container manually (to make a change and re-build the image), run: `docker container stop airtable`

*NOTE*: The program requires the PDF folder to contain the Settings folder along with the files in it as listed below.

# Folder Structures
Program Folder:
```
Main folder       - Contains all of the program's files.
├── airtable-import.py       - The main program.
├── Dockerfile               - File containing instructions for Docker to build the Docker image. (editable as text file)
├── pdf_folder_location.txt  - Contains the your location to the PDF main folder.
├── pdftotext.exe            - The program used to convert PDFs to text for further processing. Obtained from xpdfreader.com from the command line tools section on the Download page
├── README.md                - This README document.
├── requirements.txt         - Contains a list of the Python modules that must be installed for the main program to work. Docker will use this file to run `pip install` within the container image.
└── settings.ini             - Contains the settings for the program including folder locations, network share credentials, API URLs, etc.
```

PDF Folder:
```
PDF main folder   - Contains the following folders, is the place where PDFs will be placed. PDF name does not matter. If a PDF has been sitting here for a while, there may be a problem in conversionlists.py.
├── Debug            - Contains debug files (pdftotext and regexmatches .txt files) and Debug.txt (which tells you information about errors). You can place a PDF in this folder to have it generate debug files for that PDF, in order to see what the program is pulling from that file.
├── Done             - Contains finished Invoice and Order PDFs. The names for these are automatically determined from their contents.
├── Errored          - Contains PDFs that could not be properly processed for some reason. Check Debug.txt.
├── Settings         - Contains adjustable settings.
|   └── conversionlists.py    - Dictionaries containing the values needed to properly pull information from the PDFs and parse and prepare it for Airtable
├── Suspended        - Contains PDFs that have been set aside for the time being. Will mostly be supplemental PDFs that are waiting for an Invoice to be appended to. *Appending to Invoice not yet implemented*
└── Unsplit TRKINV   - Contains PDFs that consist of multiple invoices. These were placed in the main folder, then moved here after the individual orders were split out and processed.
            
```
# Program Structure

## airtable-import.py
This is the main script. When a file is placed in the PDF folder, the program runs its processes on it to pull out the relevant information for creating a record in Airtable or updating one. It then moves those .pdf files to either the Done folder or the Errored folder, depending on whether the upload to Airtable was successful.

# conversionlists.py
NOTE: A Python dictionary looks like the following:
```
dictionaryname = {Key:Value, Key2:Value2}
```
   dictionaryname is a variable that becomes a dictionary when it is assigned a value of two braces `{}`. It can contain multiple Key:Value pairs, separated by commas. In the case of conversionlists.py, the Value in each Key:Value pair is a list. In this situation, that list should contain either one string or one (or more) pairs of strings and RegEx lines. If the dictionary pair contains just one string as an entry, the entire matching line will be returned for that column. If it contains string/regex pairs, the value that is returned for the column is determined by the RegEx in the second half of the pair.

This gets pulled into the main script. It was separated out to make it easier to read and edit. It contains a few Python dictionaries, with *headerConversionList* and *dealerCodes* being the ones you will make changes to 99% of the time. The others are for determining how to pull identifier/content pairs from the pdf converted to text. Those will not need to be changed or added to unless Volvo or Mack make changes to their PDF format.

### headerConversionList
The Header conversion list is filled with multiple Key:Value pairs. The first half of each pair is the identifying line that would be seen in the .pdf file. The second half is a list (`[contents, of, list, between, brackets]`) containing the header that it would be matched to in Airtable, with optional accompanying regex entries for further processing. That list can have either just the one header entry, or it can have sets of two -- the first of which is the header and the second is the RegEx string needed to pull out specific information from the matching line in the .pdf.

#### Airtable
Airtable receives data in this format:
```
{
  "records": [
    {
      "id": "recIDplacedhere",
      "fields": {
        "Stock": "41991",
        "Year": "2020",
        "Make": "Mack",
        "Model": "LR613"
        }
    }]
} 
```

"records" contains a list of records to create/update. A record is an individual row.

"id" refers to the row ID. This is only present when updating and is obtained from Airtable's API when searching for records.

"fields" contains a list of column names and the entry that goes in that column for that record.


#### Example:
The script pulls it out into two parts, the "Identifier" which is the part that tells us what the information is, and the "Content" which is the information itself. In the following line, we know that the first 3 characters of that 6 character section (the 100 in 1002Z0) will always refer to the engine, so this is our Identifier. The part starting with MP8 is the matching Content. The section in the middle is not used because it may differ between vehicles even if the Identifier we use does not change.


Given this line in a .pdf:

```
   1002Z0    ENGINE PACKAGE, COMBUSTION       MP8-415C MACK 415HP @ 1400-170
```

A valid entry in the headerConversionList would look like this:
```
'100':['Engine Make',r'^.*? (\w+)','Engine Model',r'^(\S*)'],
```

The program will use that line in the following manner:
If the first half of the line from the .pdf (the Identifier, 100) matches the first half of an entry (dictionary Key, 100) in headerConversionList, it will begin processing the Content using the second half of the matched entry in headerConversionList (dictionary Value).

In the above example, this would be the output, with the first entry in every pair being the Airtable column header and the second entry being the cell contents:
```
{'Engine Make': 'MACK', 'Engine Model': 'MP8-415C'}
```

Taking the same line in the .pdf, if you were to use this headerConversionList entry:

```
'100':['Engine'],
```

You would end up with this:
```
{'Engine':'MP8-415C MACK 415HP @ 1400-170'}
```

To figure out how to match and refine the Content using RegEx, go to regex101.com and enter the line you want matched. In this case, you would put `MP8-415C MACK 415HP @ 1400-170` in the bottom half (along with many other entries of the same line if you can) and you would try to match it as best you can in the RegEx entry box above. As an example, take that MP8-415C line and use the Engine Make RegEx line with it (the stuff after the r and between the '' (r'in here')) and put them both in regex101.com. Use groups. Group 0 is never used in the script (always contains full match), but it does begin pulling with group 1. If multiple groups are matched, they are appended to each other (ex. r'(\d),(\d)' on the string "3,4" would become "34").


### dealerCodes
This section of conversionlists.py contains the dealer codes and their matching location. *The location must be an exact match to a location already available as an option in Airtable's Location column.*

For example, this would match the dealer code F243 to the Amarillo location.

`"F243":"Amarillo",`

If the .pdf is an invoice, airtable-import.py will recognize it as such and attempt to match the dealer code found in the document with a location in the dealerCodes dictionary, then make the relevant additions to Airtable.

# Debugging
