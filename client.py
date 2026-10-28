import hashlib
import json
import multiprocessing
import os
import socket

import message_protocol

CLIENT_NAME = "md5_client"
PROCESSES = os.cpu_count()
MAX_JOBS = None


def md5_of(number):
    return hashlib.md5(str(number).encode("utf-8")).hexdigest()


def check(number, target_hash):
    return md5_of(number) == target_hash


def search_range(start, end, target_hash):
    for number in range(start, end + 1):
        if check(number, target_hash):
            return number
    return None


def split_range(start, end, parts):
    total = end - start + 1
    parts = max(1, min(parts, total))
    base, extra = divmod(total, parts)

    ranges = []
    sub_start = start
    for i in range(parts):
        size = base + (1 if i < extra else 0)
        sub_end = sub_start + size - 1
        ranges.append((sub_start, sub_end))
        sub_start = sub_end + 1
    return ranges


def search_parallel(pool, start, end, target_hash, processes):
    tasks = [(s, e, target_hash) for s, e in split_range(start, end, processes)]
    results = pool.starmap(search_range, tasks)
    for result in results:
        if result is not None:
            return result
    return None


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.buffer = b""

    def send_message(self, message):
        data = json.dumps(message, separators=(",", ":")) + "\n"
        print(f"  -> {data.strip()}")
        self.sock.sendall(data.encode("utf-8"))

    def receive_line(self):
        while b"\n" not in self.buffer:
            if len(self.buffer) >= message_protocol.MAX_MESSAGE_SIZE:
                return None
            data = self.sock.recv(4096)
            if not data:
                return None
            self.buffer += data

        line, _, self.buffer = self.buffer.partition(b"\n")
        print(f"  <- {line.decode('utf-8', errors='replace')}")
        return line

    def receive_message(self, expected_types):
        while True:
            line = self.receive_line()
            if line is None:
                print("Connection closed by server.")
                return None

            try:
                message = json.loads(line)
            except ValueError:
                print("Server sent invalid JSON.")
                return None

            if type(message) is not dict or message.get("version") != message_protocol.PROTOCOL_VERSION:
                print("Server sent an invalid message.")
                return None

            if message.get("type") not in expected_types and message.get("type") != "ERROR":
                print(f"Ignoring unexpected message: {message.get('type')}")
                continue

            return message

    def run(self, pool):
        self.sock = socket.create_connection((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

        self.send_message(message_protocol.hello(CLIENT_NAME, PROCESSES))
        reply = self.receive_message(["WELCOME"])
        if reply is None or reply["type"] == "ERROR":
            self.sock.close()
            return

        jobs_done = 0
        while MAX_JOBS is None or jobs_done < MAX_JOBS:
            self.send_message(message_protocol.request_work())
            reply = self.receive_message(["WORK", "STOP", "NO_MORE_WORK"])
            if reply is None or reply["type"] != "WORK":
                break

            job_id = reply["job_id"]
            start = reply["start"]
            end = reply["end"]
            number = search_parallel(pool, start, end, reply["target_hash"], PROCESSES)

            if number is None:
                self.send_message(message_protocol.done(job_id, end - start + 1))
                jobs_done += 1
            else:
                self.send_message(message_protocol.found(job_id, number, md5_of(number)))
                self.receive_message(["STOP"])
                break

        self.sock.close()
        print("Disconnected.")


if __name__ == "__main__":
    host = message_protocol.PROTOCOL_IP
    port = message_protocol.DEFAULT_PORT

    with multiprocessing.Pool(PROCESSES) as pool:
        Client(host, port).run(pool)
