import os

file_signatures = {
    'jpg': {'header': b'\xff\xd8', 'footer': b'\xff\xd9'},
    'pdf': {'header': b'%PDF-', 'footer': b'%%EOF'},
    'png': {'header': b'\x89PNG\r\n\x1a\n', 'footer': b'IEND\xaeB`\x82'}
}

def carve_files(raw_data, output_dir):
    for file_type, sig in file_signatures.items():
        start = 0
        while True:
            header_index = raw_data.find(sig['header'], start)
            if header_index == -1:
                break
            footer_index = raw_data.find(sig['footer'], header_index)
            if footer_index == -1:
                break
            file_data = raw_data[header_index:footer_index + len(sig['footer'])]
            file_name = f"{file_type}_{header_index}_{footer_index}.{'jpg' if file_type == 'jpg' else file_type}"
            with open(os.path.join(output_dir, file_name), 'wb') as f:
                f.write(file_data)
            start = footer_index + len(sig['footer'])


with open('Carve1.bin', 'rb') as f:
    raw_data = f.read()

# with open('disk_image.dd', 'rb') as f:
#     raw_data = f.read()

os.makedirs('recovered_files', exist_ok=True)
carve_files(raw_data, 'recovered_files')