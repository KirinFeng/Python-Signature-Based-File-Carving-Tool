bytesToSave = b''
fileFound = False

# save the byte of Carve1.bin
with open("Carve1.bin", "rb") as f:
    byte = f.read(1)
    while byte != b'':
        if fileFound == True:
            byte = f.read(1)
            bytesToSave += byte
        else:
            print("....")
            # Do stuff with byte.
            byte = f.read(1)
            if byte == b'\xFF':
                byte = f.read(1)
                if byte == b'\xD8':
                    fileFound = True
                    bytesToSave += b"\xFF"
                    bytesToSave += b"\xD8"

file = open("test.jpg", "wb")
file.write(bytesToSave)
file.close()

# # showing all the byte of the process
# with open("Carve1.bin", "rb") as f:
#     byte = f.read(1)
#     while byte != b'':
#         byte = f.read(1)
#         print(byte)
