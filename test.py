from zipfile import ZipFile
with ZipFile("21f3000758.zip", 'r') as zip:
    zip.extractall("Unzipped")

import checksumdir
hash = checksumdir.dirhash("Unzipped")
print(hash)