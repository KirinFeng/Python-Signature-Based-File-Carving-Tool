# Digital Forensic File Carving Tool

## Overview

In digital forensics, recovering files from damaged, deleted, or corrupted storage devices is often necessary when file system metadata (allocation tables, directory entries, inode structures) is missing or intentionally destroyed. **File carving** solves this by scanning raw binary data for unique file signatures — often called **magic numbers** — that mark the start (header) and end (footer) of a file, then extracting the bytes in between.

This project implements a signature-based carving solution in Python, prioritizing transparency and educational clarity over raw performance. Existing tools such as Foremost, Scalpel, and PhotoRec are effective but largely operate as black boxes; this project's scripts are designed so every line of logic is explainable and extensible.

## Objectives

- Implement a manual proof-of-concept script (`test.py`) that extracts a single JPEG from a controlled binary sample using byte-wise scanning.
- Develop an automated, multi-format carver (`main.py`) driven by an extensible dictionary of file signatures.
- Provide full technical transparency so the logic is understandable and modifiable.
- Validate the approach against synthetic (`.bin`) and real-world (`.dd`) raw data.
- Compare results and trade-offs against established carving tools.

## How It Works

Every file format has a distinct byte sequence at its start and (often) its end. By locating these boundaries in a raw byte stream, the corresponding file can be sliced out and reconstructed with no dependency on metadata.

### Supported File Signatures

| File Type | Header (Hex) | Footer (Hex) |
|---|---|---|
| JPEG | `FF D8` | `FF D9` |
| PDF | `25 50 44 46 2D` (`%PDF-`) | `25 25 45 4F 46` (`%%EOF`) |
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `49 45 4E 44 AE 42 60 82` |

Signature sources: Gary Kessler's File Signature Table, the Wikipedia list of file signatures, and a practical carving tutorial by Hex Ninja (see [References](#references)).

## Project Structure

```
.
├── test.py              # Proof-of-concept: manual single-JPEG extraction
├── main.py               # Automated multi-format carver
├── Carve1.bin            # Sample binary test file
├── disk_image.dd          # Sample raw forensic disk image (optional)
└── recovered_files/       # Output directory for carved files
```

## Scripts

### `test.py` — Manual JPEG Extraction

A minimal proof-of-concept. Opens a binary file in read-binary (`"rb"`) mode and scans byte-by-byte for the JPEG **Start of Image (SOI)** marker `\xFF\xD8`. Once found, every subsequent byte is buffered until end-of-file and written out as `test.jpg`. This version does not check for the JPEG footer (`FFD9`) — it demonstrates the core carving concept, not a complete implementation.

```python
bytesToSave = b''
fileFound = False

# Read Carve1.bin byte-by-byte in binary mode
with open("Carve1.bin", "rb") as f:
    byte = f.read(1)
    while byte != b'':
        if fileFound == True:
            byte = f.read(1)
            bytesToSave += byte
        else:
            print("....")
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
```

### `main.py` — Automated Multi-Format Carving

Generalizes the approach: reads the entire raw file into memory, then for each entry in a `file_signatures` dictionary, repeatedly searches for header/footer pairs and slices out the matching byte ranges. Recovered files are written to `recovered_files/`, named `{file_type}_{header_offset}_{footer_offset}.{ext}` to preserve **byte-offset traceability (字节偏移可追溯性，便于后续取证核验)**.

```python
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
            file_name = f"{file_type}_{header_index}_{footer_index}.{file_type}"
            with open(os.path.join(output_dir, file_name), 'wb') as f:
                f.write(file_data)
            start = footer_index + len(sig['footer'])

with open('Carve1.bin', 'rb') as f:
    raw_data = f.read()

# with open('disk_image.dd', 'rb') as f:
#     raw_data = f.read()

os.makedirs('recovered_files', exist_ok=True)
carve_files(raw_data, 'recovered_files')
```

## Usage

**Requirements:** Python 3.10+, no external dependencies (standard library only — `os`).

```bash
# Run the manual proof-of-concept
python test.py

# Run the automated multi-format carver
python main.py
```

To carve a full disk image instead of the sample `.bin`, edit the input filename in `main.py`:

```python
with open('disk_image.dd', 'rb') as f:
    raw_data = f.read()
```

Adding support for a new file type only requires one additional entry in the `file_signatures` dictionary — no other code changes are needed.

## Algorithm

1. Load the `file_signatures` dictionary (header/footer byte sequences per format).
2. Read the entire raw binary input into memory.
3. For each supported file type, search forward for a header match.
4. From the header position, search forward for the matching footer.
5. If both are found, slice out the bytes in between (inclusive) as a candidate file.
6. Write the candidate to `recovered_files/` using the traceable naming convention.
7. Advance the scan position past the footer and repeat until no further matches remain.
8. Move to the next file type and repeat the process.

## Results

- **Test.py:** Successfully extracted a valid, viewable JPEG (`test.jpg`) from `Carve1.bin`.
- **Main.py:** Successfully recovered JPEG, PNG, and PDF files from both `Carve1.bin` and a raw `disk_image.dd`, all verified byte-for-byte via **MD5/SHA256 checksums (哈希校验，用于验证恢复文件与原始文件是否完全一致)** against the originals.
- **Fragmented files:** Only partially recovered or misaligned, since the current implementation assumes **contiguous storage (文件在磁盘上连续存储，未发生碎片化)**.

## Limitations

- Assumes non-fragmented (contiguous) file storage; fragmented files are recovered incompletely or not at all.
- Relies on precise footer detection — missing, corrupted, or variable footers (e.g., MP4, Office formats) can cause recovery failure.
- Loads the entire input file into memory, which does not scale to terabyte-sized forensic images.
- No content-based validation of recovered files, so signature collisions can produce false positives.

## Future Work

- **Fragmented file recovery** via entropy-based analysis or content-aware reassembly.
- **Format validation** post-extraction (e.g., PDF object tree, PNG chunk structure) using libraries like PyMuPDF or Pillow.
- **Memory/performance optimization** through buffered or memory-mapped I/O for large disk images.
- **GUI** built with `tkinter` or `PyQt` for non-technical users.
- **Automated forensic reporting** (recovery logs, timestamped hashes, metadata summaries) for court admissibility.
- **Additional file type support** (DOCX, MP4, ZIP, etc.).

## Comparison with Existing Tools

| Tool | Strengths | Trade-offs |
|---|---|---|
| Foremost | Stable, efficient | Static config, limited flexibility |
| Scalpel | Multithreaded, faster | Non-intuitive config, hard to modify internal logic |
| PhotoRec | 480+ formats, structure validation | Opaque internals, hard to customize |
| **This project** | Fully transparent, easily extensible, educational | Lower raw performance, no fragmentation handling |

## References

1. G. C. Kessler, "File Signatures." https://www.garykessler.net/library/file_sigs.html
2. Wikipedia contributors, "List of file signatures," Wikipedia, Apr. 21, 2025. https://en.wikipedia.org/wiki/List_of_file_signatures
3. The Hex Ninja, "Practical exercise: image carving." https://www.thehexninja.com/2017/12/practical-exercise-image-carving.html
4. Security in mind, "Digital Forensics - File signatures - Explanation," YouTube, Mar. 21, 2022. https://www.youtube.com/watch?v=gNRNubRXduA
5. Security in mind, "Digital Forensics - USB File Extraction," YouTube, Mar. 25, 2022. https://www.youtube.com/watch?v=dGCQzAPPjvA
6. Security in mind, "Digital Forensics - File Carving," YouTube, Mar. 23, 2022. https://www.youtube.com/watch?v=QmiXZog8LEs
