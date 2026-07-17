import py_compile
import pathlib

files = [
    pathlib.Path(r'd:/VSCode_projects/ssugt-calls/ssugt-outgoing-calls/src/api/outgoing_calls/services/control_call_queue.py'),
    pathlib.Path(r'd:/VSCode_projects/ssugt-calls/ssugt-outgoing-calls/tests/test_control_call_queue.py'),
]
for path in files:
    py_compile.compile(str(path), doraise=True)
    print(f'compiled {path}')
