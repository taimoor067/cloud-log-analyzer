import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def split_file(filepath, chunk_size=100):
    chunks = []
    with open(filepath, 'r', errors='ignore') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]  # skip empty lines
    if not lines:
        raise ValueError("Log file is empty")
    for i in range(0, len(lines), chunk_size):
        chunks.append(lines[i:i + chunk_size])
    return chunks, len(lines)


def map_chunk(chunk):
    results = []
    for line in chunk:
        # Pattern 1: Standard Apache/Nginx — "GET /path HTTP/1.1" 200
        status = re.search(r'" (\d{3}) ', line)

        # Pattern 2: Fallback — any 3-digit status code in line
        if not status:
            status = re.search(r'\b([1-5]\d{2})\b', line)

        if status:
            code = status.group(1)
            results.append((f"HTTP_{code}", 1))

        # Pattern 1: Standard timestamp :HH:MM:SS
        hour = re.search(r':(\d{2}):\d{2}:\d{2}', line)

        # Pattern 2: Fallback — any time HH:MM
        if not hour:
            hour = re.search(r'\b(\d{2}):\d{2}\b', line)

        if hour:
            h = hour.group(1)
            # only valid hours 00-23
            if 0 <= int(h) <= 23:
                results.append((f"Hour_{h}", 1))

    return results


def shuffle(mapped_results):
    grouped = defaultdict(list)
    for pairs in mapped_results:
        for key, value in pairs:
            grouped[key].append(value)
    return grouped


def reduce_group(item):
    key, values = item
    return (key, sum(values))


def run_mapreduce(filepath):
    chunks, total_lines = split_file(filepath)

    with ThreadPoolExecutor() as executor:
        mapped_results = list(executor.map(map_chunk, chunks))

    grouped = shuffle(mapped_results)

    if not grouped:
        raise ValueError(
            f"No recognizable log patterns found in file. "
            f"File had {total_lines} lines but none matched Apache/Nginx format. "
            f"Expected format: 127.0.0.1 - - [10/Oct/2023:10:12:01 +0000] "
            f'"GET /index.html HTTP/1.1" 200 1540'
        )

    with ThreadPoolExecutor() as executor:
        final_results = list(executor.map(reduce_group, grouped.items()))

    return dict(sorted(final_results, key=lambda x: x[1], reverse=True))