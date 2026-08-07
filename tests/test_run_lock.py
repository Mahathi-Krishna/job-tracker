from utils.run_lock import RunLock


first = RunLock()
second = RunLock()


print(
    "First:",
    first.acquire()
)

print(
    "Second:",
    second.acquire()
)


first.release()


print(
    "After release:",
    second.acquire()
)


second.release()