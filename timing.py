import multiprocessing
import os
import time

from client import search_parallel, search_range

NEVER_MATCHES = "0" * 32


def main():
    start = 1000000000
    end = 1001999999
    processes = os.cpu_count()

    count = end - start + 1
    print(f"Range {start}-{end} ({count} numbers)")

    t0 = time.perf_counter()
    search_range(start, end, NEVER_MATCHES)
    serial_time = time.perf_counter() - t0
    print(f"Serial:          {serial_time:.2f} s")

    with multiprocessing.Pool(processes) as pool:
        t0 = time.perf_counter()
        search_parallel(pool, start, end, NEVER_MATCHES, processes)
        parallel_time = time.perf_counter() - t0
    print(f"{processes} processes:     {parallel_time:.2f} s")
    print(f"Speedup:         {serial_time / parallel_time:.2f}x")


if __name__ == "__main__":
    main()
