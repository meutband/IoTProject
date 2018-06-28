from pymodbus.client.sync import ModbusSerialClient
from Hologram.HologramCloud import HologramCloud
from interruptingcow import timeout
import os
import time
import json


def initial_boot():

    file = open('sequences.txt','a')
    file.write('\nInitial Boot at ' + time.strftime('%H:%M') + '\n')
    file.close()

    time.sleep(30)

    try:

        with timeout(300, exception=RuntimeError):

            # Connect to network
            hologram = connect_hologram()

            if hologram == 'Moo':
                raise RuntimeError

    except RuntimeError:

        file = open('error_messages.txt','a')
        file.write('MOOOOOOOOOOOOOO Connection:' + time.strftime('%Y-%m-%d %H:%M') + '\n')
        file.close()

        os.system('sudo hologram modem disconnect')
        os.system('sudo reboot')

    time.sleep(45)

    # Set timezone
    os.environ['TZ'] = 'US/Central'
    time.tzset()

    # Disconnect from network
    os.system('sudo hologram modem disconnect')


def run_modbus(t):

    try:

        # Connect to altonic meter
        client = ModbusSerialClient(method='rtu', port='/dev/ttyUSB0',
                                    stopbits=1, bytesize=8, parity='N', baudrate=9600)
        client.connect()

        registers = [0,1,3,17,18]
        status = [t]

        # Read the registries, append to status list.
        for reg in registers:
            result = client.read_holding_registers(reg, 1, unit=1)
            status.append(str(result.registers[0]))

        file = open('sequences.txt','a')
        file.write('Modbus Read at ' + time.strftime('%H:%M') + '\n')
        file.close()

        return status

    except RuntimeError:

        return 'Moo'

    except Exception as e:

        # Save error in file
        file = open('error_messages.txt','a')
        file.write('Error: ' + str(e.message) +  ' at ' + time.strftime('%Y-%m-%d %H:%M') + '\n')
        file.close()

        try:
            with timeout(60, exception=RuntimeError):
                hologram = connect_hologram()
                if hologram == 'Moo':
                    raise RuntimeError

        except RuntimeError:
            os.system('sudo hologram modem disconnect')
            os.system('sudo reboot')

        mess = hologram.sendMessage(str(e.message), topics ='ModbusError', timeout=30)
        os.system('sudo hologram modem disconnect')

        if mess != 0:
            os.system('sudo reboot')

        time.sleep(900)

        t = time.strftime('%Y-%m-%d %H:%M:%S')
        status = run_modbus(t)
        return status


def connect_hologram():

    try:

        cred = {'devicekey':''}
        hologram = HologramCloud(cred, network='cellular')

        network = hologram.network.connect(timeout=120)

        if network == False:

            os.system('sudo hologram modem disconnect')
            time.sleep(30)

            hologram = connect_hologram()
            return hologram

        file = open('sequences.txt','a')
        file.write('Connection Successful at ' + time.strftime('%H:%M') + '\n')
        file.close()

        return hologram

    except RuntimeError:

        return 'Moo'

    except Exception as e:

        # Save error in file
        file = open('error_messages.txt','a')
        file.write('Error: ' + str(e.message) +  ' at ' + time.strftime('%Y-%m-%d %H:%M') + '\n')
        file.close()

        os.system('sudo hologram modem disconnect')
        time.sleep(30)

        hologram = connect_hologram()
        return hologram


def send_hologram(status, hologram):

    try:

        # Send message with Losant tag (for Losant)
        names = ['Time', 'RPM', 'Hours', 'Dis', 'Int', 'DC']
        data = {}

        for i, name in enumerate(names):
            data[name] = status[i]

        mess = hologram.sendMessage(json.dumps(data), topics ='Losant', timeout=45)

        if mess != 0:

            file = open('error_messages.txt','a')
            file.write('Failed to send data, code ' + str(mess) + ': ' + time.strftime('%Y-%m-%d %H:%M') + '\n')
            file.close()

            time.sleep(30)

            upload = send_hologram(status, hologram)
            return upload

        file = open('sequences.txt','a')
        file.write('Message Uploaded at ' + time.strftime('%H:%M') + '\n')
        file.close()

        return True

    except RuntimeError:

        return 'Moo'

    except Exception as e:

        # Save error in file
        file = open('error_messages.txt','a')
        file.write('Error: ' + str(e.message) +  ' at ' + time.strftime('%Y-%m-%d %H:%M') + '\n')
        file.close()

        time.sleep(30)

        upload = send_hologram(status, hologram)
        return upload



if __name__ == '__main__':

    # Run initial boot sequence
    initial_boot()

    t1 = time.time()

    file = open('sequences.txt','a')
    file.write('First Run at ' + time.strftime('%m-%d %H:%M') + '\n')
    file.close()

    while True:

        t2 = time.time()
        if t2 - t1 > 64800:
            os.system('sudo hologram modem disconnect')
            os.system('sudo reboot')

        try:

            with timeout(1200, exception=RuntimeError):

                # Connect to altronic meter, read registers
                t = time.strftime('%Y-%m-%d %H:%M:%S')
                status = run_modbus(t)

                if status == 'Moo':
                    raise RuntimeError

        except RuntimeError:

            file = open('error_messages.txt','a')
            file.write('MOOOOOOOOOOOOOO Modbus:' + time.strftime('%Y-%m-%d %H:%M') + '\n')
            file.close()

            os.system('sudo hologram modem disconnect')
            os.system('sudo reboot')

        try:

            with timeout(300, exception=RuntimeError):

                # Connect to network
                hologram = connect_hologram()

                if hologram == 'Moo':
                    raise RuntimeError

        except RuntimeError:

            file = open('error_messages.txt','a')
            file.write('MOOOOOOOOOOOOOO Connection:' + time.strftime('%Y-%m-%d %H:%M') + '\n')
            file.close()

            os.system('sudo hologram modem disconnect')
            os.system('sudo reboot')

        try:

            with timeout(150, exception=RuntimeError):

                # Send data to Hologram
                upload = send_hologram(status, hologram)

                if upload == 'Moo':
                    raise RuntimeError

        except RuntimeError:

            file = open('error_messages.txt','a')
            file.write('MOOOOOOOOOOOOOO Sending Data:' + time.strftime('%Y-%m-%d %H:%M') + '\n')
            file.close()

            os.system('sudo hologram modem disconnect')
            os.system('sudo reboot')


        # Disconnect from the network
        os.system('sudo hologram modem disconnect')

        # Wait 15 mintues
        time.sleep(900)

        file = open('sequences.txt','a')
        file.write('Next Run at ' + time.strftime('%H:%M') + '\n')
        file.close()
