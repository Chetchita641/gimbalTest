import socket
import argparse
import keyboard
import asyncio
import time

GIMBAL_IP = "192.168.1.6"
GIMBAL_PORT = 4000
BUFFER_SIZE = 512
ABS_MAX = 3000
DELAY = 5

MovementTrans = {'u': 'TO100\n', 'd': 'TO-100\n', 'l': 'PO-100\n', 'r': 'PO100\n'}

class Gimbal():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.response = ""

        asyncio.run(self.power_on())
        
    def close(self):
        time.sleep(DELAY)
        self.home()
        self.socket.close()

    async def power_on(self):
        try:
            self.socket.connect((GIMBAL_IP, GIMBAL_PORT))
        except Exception as e:
            print(e)
        self.home()
        await asyncio.sleep(DELAY)

    def get_response(self):
        output = self.response
        self.response = ""
        return output

    def home(self):
        signal = 'RE\nA\n'
        self.socket.send(signal.encode())

    def send_movement(self, movement):
        signal = MovementTrans[movement]
        if not signal:
            print("signal not found")
            return
        self.socket.send(signal.encode())

    async def full_rotation(self):
        top_left = "TP{}\nPP{}\nA\n".format(ABS_MAX, ABS_MAX)
        top_right = "TP{}\nPP{}\nA\n".format(ABS_MAX, -ABS_MAX)
        bottom_left = "TP{}\nPP{}\nA\n".format(-ABS_MAX, ABS_MAX)
        bottom_right = "TP{}\nPP{}\nA\n".format(-ABS_MAX, -ABS_MAX)
        sequence = [top_left, top_right, bottom_left, bottom_right]

        await self.send_sequence(sequence)

    async def send_sequence(self, sequence):
        for signal in sequence:
            self.socket.send(signal.encode())
            await asyncio.sleep(DELAY)

    """
        top = "TP{}\nA\n".format(ABS_MAX)
        bottom = "TP{}\nA\n".format(-ABS_MAX)
        left = "PP{}\nA\n".format(-ABS_MAX)
        right = "PP{}\nA\n".format(ABS_MAX)
        sequence = [top, bottom, left, right]
    """



parser = argparse.ArgumentParser()
parser.add_argument('-r', default=1, dest='reps', type=int, help="Number of repetitions")
parser.add_argument('-t', default=0, dest='timespan', type=int, help='Amount of time (in sec) to do tests')
parser.add_argument('-c', default=False, action='store_true', dest='continuous', help='Continuous rotations until program is shut down')
parser.add_argument('-m', default=False, action='store_true', dest='manual', help="Manual control of the gimbal")

args = parser.parse_args()
reps = args.reps
timespan = args.timespan
continuous = args.continuous
manual = args.manual

gimbal = Gimbal()

async def main():
    if manual:
        while True:
            print("use WASD to move up, left, down, or right. Press Ctrl-C to exit")
            keyboard.on_press_key('w', gimbal.send_movement, args=('u'))
            keyboard.add_hotkey('a', gimbal.send_movement, args=('l'))
            keyboard.add_hotkey('s', gimbal.send_movement, args=('d'))
            keyboard.add_hotkey('d', gimbal.send_movement, args=('r'))
            response = gimbal.get_response()
            if response:
                print(response)
            keyboard.wait()

    if continuous:
        print("Press Ctrl-C to exit the program")
        while True:
            await gimbal.full_rotation()
    elif timespan > 0:
        end_time = time.time() + timespan
        while time.time() <= end_time:
            await gimbal.full_rotation()
        gimbal.close()
    elif reps > 0:
        for _ in range(reps):
            await gimbal.full_rotation()

try:
    asyncio.run(main())
except:
    gimbal.close()