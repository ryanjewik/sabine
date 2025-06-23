import gzip
import xml.etree.ElementTree as ET


#decompresses the fandom files and saves the xml files

# File paths
GZ_FILE = 'valorant_esports_pages.xml.gz' #valorant_pages.xml.gz
XML_FILE = 'valorant_esports_pages.xml' #valorant_pages.xml

# --- Step 1: Decompress the GZ file ---
def decompress_gz(source_path, target_path):
    print(f"Decompressing {source_path}...")
    with gzip.open(source_path, 'rb') as f_in, open(target_path, 'wb') as f_out:
        f_out.write(f_in.read())
    print(f"Decompressed to {target_path}")

# --- Step 2: Parse XML and extract data ---
def parse_xml(path):
    print(f"Parsing {path}...")
    tree = ET.parse(path)
    root = tree.getroot()

    # Example: Print first 10 page titles
    for i, page in enumerate(root.findall('.//page')):
        title = page.findtext('title')
        print(f"[{i+1}] {title}")
        if i >= 9:
            break

# --- Run ---
if __name__ == "__main__":
    decompress_gz(GZ_FILE, XML_FILE)
    parse_xml(XML_FILE)
