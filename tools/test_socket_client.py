import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.on('open_tab')
def on_open_tab(data):
    print('OPEN_TAB:', data)

@sio.event
def system_log(data):
    print('LOG:', data)

@sio.event
def activity_state(data):
    print('ACTIVITY:', data)

@sio.event
def disconnect():
    print('Disconnected')

if __name__ == '__main__':
    url = 'http://localhost:8000'
    sio.connect(url, auth={'token': 'jarvis-local-secret'})
    time.sleep(1)
    cmds = [
        'open instagram profile of avneetkaur_13',
        'tmkoc episode no 126'
    ]
    for c in cmds:
        print('Sending:', c)
        sio.emit('process_command', { 'command': c })
        time.sleep(2)
    time.sleep(3)
    sio.disconnect()
