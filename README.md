# LegoDownloader
Script to download LEGO instructions

LEGO hosts instructional PDFs for most sets on its website. This script will parse through the sets and download both the instruction PDF(s) as well as the set image. 

Folder structure is based on themes with the set the set ID, name, and release year making up the directory names. Instruction booklets are numbered and downloaded to the product's directory.

example
![Folder Structure](https://github.com/luke-eisenbraun/LegoDownloader/blob/master/lego.png)

To Run:
  * Change the storage root on [line 12](https://github.com/luke-eisenbraun/LegoDownloader/blob/master/instruction_downloader.py#L12)
  * Grab your UAID from a lego.com cookie and set on [line 17](https://github.com/luke-eisenbraun/LegoDownloader/blob/master/instruction_downloader.py#L17)
  
  * `python3 instruction_downloader.py`
