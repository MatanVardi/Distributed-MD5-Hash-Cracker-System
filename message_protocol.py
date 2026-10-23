DEFAULT_PORT = 50505
MAX_MESSAGE_SIZE = 4096
PROTOCOL_VERSION = 1


def hello(client_name, processes):
    return {
        "version": PROTOCOL_VERSION,
        "type": "HELLO",
        "client_name": client_name,
        "processes": processes,
    }


def welcome(server_name, hash_algorithm, target_hash):
    return {
        "version": PROTOCOL_VERSION,
        "type": "WELCOME",
        "server_name": server_name,
        "algorithm": hash_algorithm,
        "target_hash": target_hash,
    }


def request_work():
    return {"version": PROTOCOL_VERSION, "type": "REQUEST_WORK"}


def work(job_id, start, end, target_hash, lease_seconds):
    return {
        "version": PROTOCOL_VERSION,
        "type": "WORK",
        "job_id": job_id,
        "start": start,
        "end": end,
        "target_hash": target_hash,
        "lease_seconds": lease_seconds,
    }


def done(job_id, checked):
    return {
        "version": PROTOCOL_VERSION,
        "type": "DONE",
        "job_id": job_id,
        "checked": checked,
    }


def found(job_id, number, calculated_hash):
    return {
        "version": 1,
        "type": "FOUND",
        "job_id": job_id,
        "number": number,
        "calculated_hash": calculated_hash,
    }


def stop(number):
    return {"version": PROTOCOL_VERSION, "type": "STOP", "number": number}


def no_more_work():
    return {"version": PROTOCOL_VERSION, "type": "NO_MORE_WORK"}


def error(code, message):
    return {
        "version": PROTOCOL_VERSION,
        "type": "ERROR",
        "code": code,
        "message": message,
    }
