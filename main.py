import asyncio
from bleak import BleakScanner, BleakClient
from math import log

async def main():
    devices = await BleakScanner.discover(return_adv=True)
    print(devices)
    pavlok = None
    for d in devices:
        if devices[d][1].local_name == "Pavlo":
            pavlok = d

    if pavlok:
        print("Found pavlok, connecting...")
    else:
        print("Can't find pavlok")

    async with BleakClient(pavlok) as client:
        print("connected")
        blah = await client.read_gatt_char(2)
        print(blah)




def d_calc(value):  # mathmatical function to calculate duration in hex when given desired number of seconds (see readme for more explanation)
    return format(int(round(log(value / 0.104) / 0.075)), 'x').zfill(
        2)  # take duration in seconds, convert to hex value for device


def vibrate(level, count=1, duration_on=0.65, gap=0.65):  # send vibrate command to Pavlok 2

    # if self.value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
    count = str(count)
    level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
    duration_on = d_calc(duration_on)
    gap = d_calc(gap)


    value = "8" + count + "0c" + level + duration_on + gap  # format into packet to be sent to Pavlok 2
    print(value)


print(vibrate(1))

asyncio.run(main())

