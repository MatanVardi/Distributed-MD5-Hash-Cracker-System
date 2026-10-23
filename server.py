import hashlib
import json
import socket
import threading
import time

import message_protocol


class Server:
    def __init__(self):

        self.name = "Server"
        self.algorithm = "md5"
        self.target_hash = "5901470673b7e50ce98c22335986776b"

        self.range_end = 10000000
        self.range_start = 0
        self.chunk_size = 100000
        self.lease_seconds = 60

        self.jobs = {}
        self.next_job_id = 1
        self.found = None

        self.lock = threading.Lock()

    def send_message(self, sock, message):
        data = json.dumps(message, separators=(",", ":")) + "\n"
        print(f"  -> {data.strip()}")
        sock.sendall(data.encode("utf-8"))

    def receive_message(self, reader):
        line = reader.readline(message_protocol.MAX_MESSAGE_SIZE)
        if not line:
            return None
        return json.loads(line)

    def handle_request_work(self, sock, message):
        with self.lock:
            if self.found is not None:
                reply = message_protocol.stop(self.found)

            elif self.range_start > self.range_end:
                reply = message_protocol.no_more_work()

            else:
                start = self.range_start
                end = min(start + self.chunk_size - 1, self.range_end)

                job_id = f"job-{self.next_job_id:06d}"
                self.next_job_id += 1

                self.jobs[job_id] = {
                    "start": start,
                    "end": end,
                    "client": sock.getpeername(),
                    "deadline": time.time() + self.lease_seconds,
                    "status": "assigned",
                }

                self.range_start = end + 1
                reply = message_protocol.work(
                    job_id, start, end, self.target_hash, self.lease_seconds
                )

        self.send_message(sock, reply)

    def handle_hello(self, sock, message):
        if "client_name" not in message or "processes" not in message:
            self.send_message(
                sock, message_protocol.error("BAD_HELLO", "Missing fields")
            )
            return False

        with self.lock:
            self.clients[sock.getpeername()] = {
                "name": message["client_name"],
                "processes": message["processes"],
            }

        self.send_message(
            sock, message_protocol.welcome(self.name, self.algorithm, self.target_hash)
        )
        return True

    def handle_done(self, sock, message):
        with self.lock:
            job = self.jobs.get(message["job_id"])
            if job is not None:
                job["status"] = "done"

    def handle_found(self, sock, message):
        job = self.jobs.get(message.get("job_id"))
        number = message["number"]

        calculated = hashlib.new(self.algorithm, str(number).encode()).hexdigest()

        if job is None:
            self.send_message(sock, message_protocol.error("UNKNOWN_JOB", "No such job"))
            return

        if calculated == self.target_hash:
            with self.lock:
                self.found = number
            self.send_message(sock, message_protocol.stop(number))

        else:
            self.send_message(
                sock,
                message_protocol.error("WRONG_ANSWER", f"{number} is not the answer"),
            )

    def handle_client(self, sock, address):
        message = message_protocol.hello(client_name="client", processes=8)
        data = json.dumps(message, separators=(",", ":")) + "\n"
        sock.sendall(data.encode("utf-8"))
        client_connected = True

        while client_connected:
            received_message = self.receive_message()
            handler_type = received_message["type"]

            if handler_type == "STOP":
                print("Client disconnecting.")
                sock.close()

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(
            (message_protocol.PROTOCOL_IP, message_protocol.DEFAULT_PORT)
        )
        server_socket.listen()

        while True:
            (client_socket, client_address) = server_socket.accept()
            print(f"\nClient connected from {client_address}")
            threading.Thread(
                target=self.handle_client, args=(client_socket,), daemon=True
            ).start()


if __name__ == "__main__":
    Server().run()
