DEFAULT_PORT = 50505
MAX_MESSAGE_SIZE = 4096


class Protocol:
    def make_hello(self, client_name, processes):

        return {
            "version": 1,
            "type": "HELLO",
            "client_name": client_name,
            "processes": processes,
        }

    def make_welcome(self, server_name, hash_algorithm, target_hash):

        return {
            "version": 1,
            "type": "WELCOME",
            "server_name": server_name,
            "algorithm": hash_algorithm,
            "target_hash": target_hash,
        }

    def request_work(self):
        return {"version": 1, "type": "REQUEST_WORK"}

    def work(self, job_id, start, end, target_hash, lease_seconds):
        return {
            "version": 1,
            "type": "WORK",
            "job_id": job_id,
            "start": start,
            "end": end,
            "target_hash": target_hash,
            "lease_seconds": lease_seconds,
        }
