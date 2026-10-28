import hashlib
import json
import socket

import message_protocol

TARGET_HASH = "3fd5c2a0df1ce9dc01f0698adc57c72b"
SEARCH_START = 1000000000
SEARCH_END = 9999999999
CHUNK_SIZE = 100000
PORT = message_protocol.DEFAULT_PORT
SERVER_NAME = "md5_server"

FIELDS = {
    "HELLO": {"client_name": str, "processes": int},
    "REQUEST_WORK": {},
    "DONE": {"job_id": str, "checked": int},
    "FOUND": {"job_id": str, "number": int, "calculated_hash": str},
}


class Server:
    def __init__(self):

        self.name = SERVER_NAME
        self.algorithm = "md5"
        self.target_hash = TARGET_HASH

        self.range_end = SEARCH_END
        self.range_start = SEARCH_START
        self.chunk_size = CHUNK_SIZE
        self.lease_seconds = 60

        self.jobs = {}
        self.next_job_id = 1
        self.found = None

        self.buffer = b""

    def send_message(self, sock, message):
        data = json.dumps(message, separators=(",", ":")) + "\n"
        print(f"  -> {data.strip()}")
        sock.sendall(data.encode("utf-8"))

    def receive_message(self, sock):
        while b"\n" not in self.buffer:
            if len(self.buffer) >= message_protocol.MAX_MESSAGE_SIZE:
                line = self.buffer
                self.buffer = b""
                return line
            try:
                data = sock.recv(4096)
            except OSError:
                return None
            if not data:
                return None
            self.buffer += data

        line, _, self.buffer = self.buffer.partition(b"\n")
        print(f"  <- {line.decode('utf-8', errors='replace')}")
        return line

    def check_message(self, line):
        if len(line) + 1 > message_protocol.MAX_MESSAGE_SIZE:
            return None, message_protocol.error("INVALID_MESSAGE", "message too long")

        try:
            message = json.loads(line)
        except ValueError:
            return None, message_protocol.error("INVALID_JSON", "could not parse JSON")

        if type(message) is not dict:
            return None, message_protocol.error("INVALID_MESSAGE", "message must be a JSON object")
        if "version" not in message:
            return None, message_protocol.error("INVALID_MESSAGE", "missing field: version")
        if message["version"] != message_protocol.PROTOCOL_VERSION:
            return None, message_protocol.error("UNSUPPORTED_VERSION", "only version 1 is supported")
        if message.get("type") not in FIELDS:
            return None, message_protocol.error("INVALID_MESSAGE", f"unknown type: {message.get('type')}")

        for field, field_type in FIELDS[message["type"]].items():
            if field not in message:
                return None, message_protocol.error("INVALID_MESSAGE", f"missing field: {field}")
            if type(message[field]) is not field_type:
                return None, message_protocol.error("INVALID_MESSAGE", f"wrong type for field: {field}")

        if message["type"] == "HELLO" and not 1 <= len(message["client_name"]) <= 40:
            return None, message_protocol.error("INVALID_MESSAGE", "client_name must be 1-40 chars")

        return message, None

    def handle_hello(self, sock, message):
        print(f"Client '{message['client_name']}' will use {message['processes']} processes")
        self.send_message(
            sock, message_protocol.welcome(self.name, self.algorithm, self.target_hash)
        )

    def handle_request_work(self, sock, message):
        if self.found is not None:
            reply = message_protocol.stop(self.found)

        elif self.range_start > self.range_end:
            reply = message_protocol.no_more_work()

        else:
            start = self.range_start
            end = min(start + self.chunk_size - 1, self.range_end)
            self.range_start = end + 1

            job_id = f"job-{self.next_job_id:06d}"
            self.next_job_id += 1

            self.jobs[job_id] = {"start": start, "end": end, "status": "assigned"}
            reply = message_protocol.work(
                job_id, start, end, self.target_hash, self.lease_seconds
            )

        self.send_message(sock, reply)

    def handle_done(self, sock, message):
        job = self.jobs.get(message["job_id"])
        if job is None:
            self.send_message(sock, message_protocol.error("UNKNOWN_JOB", "No such job"))
            return

        job["status"] = "done"

    def handle_found(self, sock, message):
        job = self.jobs.get(message["job_id"])
        number = message["number"]

        if job is None:
            self.send_message(sock, message_protocol.error("UNKNOWN_JOB", "No such job"))
            return

        if not job["start"] <= number <= job["end"]:
            self.send_message(
                sock, message_protocol.error("INVALID_RESULT", f"{number} is not in the job range")
            )
            return

        calculated = hashlib.md5(str(number).encode("utf-8")).hexdigest()

        if calculated == self.target_hash:
            job["status"] = "found"
            self.found = number
            self.send_message(sock, message_protocol.stop(number))

        else:
            self.send_message(
                sock, message_protocol.error("INVALID_RESULT", f"{number} is not the answer")
            )

    def handle_client(self, sock):
        self.buffer = b""
        said_hello = False

        while True:
            line = self.receive_message(sock)
            if line is None:
                print("Client disconnected.")
                break

            message, error = self.check_message(line)

            if error is not None:
                self.send_message(sock, error)
                if not said_hello or len(line) >= message_protocol.MAX_MESSAGE_SIZE:
                    break

            elif message["type"] == "HELLO":
                self.handle_hello(sock, message)
                said_hello = True

            elif not said_hello:
                self.send_message(
                    sock, message_protocol.error("INVALID_MESSAGE", "HELLO must be the first message")
                )
                break

            elif message["type"] == "REQUEST_WORK":
                self.handle_request_work(sock, message)

            elif message["type"] == "DONE":
                self.handle_done(sock, message)

            else:
                self.handle_found(sock, message)

        sock.close()

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.listen()
        print("Server is listening")

        while True:
            (client_socket, client_address) = server_socket.accept()
            print(f"\nClient connected from {client_address}")
            self.handle_client(client_socket)


if __name__ == "__main__":
    Server().run()
