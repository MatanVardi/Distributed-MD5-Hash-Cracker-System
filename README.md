# MD5 Project - Part A

Python 3.11. Default port 50505.

## Files

- message_protocol.py - the messages, sending/receiving and checking messages
- server.py - the server
- client.py - the client
- timing.py - compares serial vs multiprocessing time

## How to run

    python server.py
    python client.py

Server settings are at the top of server.py: TARGET_HASH, SEARCH_START, SEARCH_END, CHUNK_SIZE, PORT, SERVER_NAME.

The client asks for the server IP and port (Enter = 127.0.0.1 and 50505).
Other client settings are at the top of client.py: CLIENT_NAME, PROCESSES, MAX_JOBS.

## Experiments

Local check: SEARCH_START = 1010100000, SEARCH_END = 1010102000, default hash.

Experiment 1: TARGET_HASH = 6797b015231191ea9da108912165cdf0, SEARCH_START = 1000000000.

Experiment 2: TARGET_HASH = a7709d792b82ae2d16ccdbbdde7bf30f, SEARCH_START = 1000000000.
Run one client with MAX_JOBS = 3, then set MAX_JOBS = None and run a second client.

Timing:

    python timing.py

## Tests

| Test | Sent | Reply |
|---|---|---|
| Normal start | HELLO | WELCOME |
| Ask for job | REQUEST_WORK | WORK |
| Job done | DONE | nothing |
| Right answer | FOUND | STOP |
| Range finished | REQUEST_WORK | NO_MORE_WORK |
| Already found | REQUEST_WORK | STOP |
| Bad JSON | `{"version":1,` | INVALID_JSON |
| Wrong version | version 2 | UNSUPPORTED_VERSION |
| Missing field | DONE without job_id | INVALID_MESSAGE |
| REQUEST_WORK before HELLO | REQUEST_WORK | INVALID_MESSAGE |
| Unknown job_id | DONE job-999999 | UNKNOWN_JOB |
| Wrong FOUND number | FOUND wrong number | INVALID_RESULT |
| Message over 4096 bytes | long line | INVALID_MESSAGE |
