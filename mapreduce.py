import multiprocessing
import re
from collections import defaultdict

def split_file(filepath, chunk_size=100):
    chunks = []
    with open(filepath, 'r', errors='ignore') as f:
        lines = f.readlines()
    for i in range(0, len(lines), chunk_size):
        chunks.append(lines[i:i + chunk_size])
    return chunks

def map_chunk(chunk):
    results = []
    for line in chunk:
        status = re.search(r'" (\d{3}) ', line)
        if status:
            code = status.group(1)
            results.append((f"HTTP_{code}", 1))
        hour = re.search(r':(\d{2}):\d{2}:\d{2}', line)
        if hour:
            h = hour.group(1)
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
    chunks = split_file(filepath)
    with multiprocessing.Pool() as pool:
        mapped_results = pool.map(map_chunk, chunks)
    grouped = shuffle(mapped_results)
    with multiprocessing.Pool() as pool:
        final_results = pool.map(reduce_group, grouped.items())
    return dict(sorted(final_results, key=lambda x: x[1], reverse=True))