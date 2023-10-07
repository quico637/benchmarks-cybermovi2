import threading

NUM_THREADS = 6
import time

# Define a function that represents a thread's task
def useless_operations(thread_id):
    while True:
        # print(f"Thread {thread_id}: Doing useless operations...")
        # You can perform some dummy calculations or operations here
        # For simplicity, we'll just sleep for a while
        a = 223233 * 223232
        b = 223233 / 223232
        c = a + b

# Create and start six threads
threads = []
for i in range(NUM_THREADS):
    thread = threading.Thread(target=useless_operations, args=(i,))
    thread.daemon = True  # Set the thread as a daemon so it exits when the main program exits
    thread.start()
    threads.append(thread)

try:
    # Keep the main thread running while the other threads run in the background
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Terminating...")
    exit(0)

# Wait for all threads to finish (although they are daemons and should exit with the main program)
for thread in threads:
    thread.join()

print("Program terminated.")

