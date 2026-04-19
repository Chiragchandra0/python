import easyocr

reader = easyocr.Reader(['en'])
result = reader.readtext('stats.jpeg')

print("EID = ", result[6][1])