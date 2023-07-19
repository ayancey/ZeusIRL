import asyncio
from bleak import BleakClient
import time
from threading import Thread
from math import log
from bottle import route, run, template, request

address = "DD:18:6E:26:BD:D9"
MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"

ready = False

async def main(address):
    async with BleakClient(address) as client:
        print("connected")

        features = {}

        for characteristic in client.services.characteristics.values():
            if characteristic.description in ["Vibe", "Beep", "Zap"]:
                features[characteristic.description] = characteristic


        loop = asyncio.get_event_loop()
        loop.run_forever()

        # await client.write_gatt_char(15, bytes.fromhex("810c0a1818"))
        # client.write_gatt_char()
        # blah = await client.read_gatt_char(2)
        # print(blah)
        # blah = await client.read_gatt_char(7)
        # print(blah)
        #
        #model_number = await client.read_gatt_char(MODEL_NBR_UUID)
        #print("Model Number: {0}".format("".join(map(chr, model_number))))

#asyncio.run(main(address))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    def bleak_thread(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
    t = Thread(target=bleak_thread, args=(loop,))
    t.start()

    client = BleakClient(address)

    future = asyncio.run_coroutine_threadsafe(client.connect(), loop)

    real_client = future.result(10)

    features = {}
    for characteristic in client.services.characteristics.values():
        if characteristic.description in ["Vibe", "Beep", "Zap"]:
            features[characteristic.description] = characteristic

    async def send_vibe():
        await client.write_gatt_char(features["Vibe"], bytes.fromhex("810c0a1818"), response=True)

    async def send_beep():
        await client.write_gatt_char(features["Beep"], bytes.fromhex("810c0a1818"), response=True)


    def d_calc(value):  # mathmatical function to calculate duration in hex when given desired number of seconds (see readme for more explanation)
        return format(int(round(log(value / 0.104) / 0.075)), 'x').zfill(
            2)  # take duration in seconds, convert to hex value for device


    def value_check(l, c, d=0.65,
                    g=0.65):  # check parameters before sending information to Pavlok 2 (these limits imposed as Pavlok performs unexpectedly outside of them)
        if l < 0 or l > 10:  # Level should not exceed 10 or be negative
            return False
        elif c > 7:  # Count should not exceed 7 (temporary cap, to be removed)
            return False
        elif d > 10 or g > 10 or d < 0.11 or g < 0.11:  # Duration on and duration of gap cannot exceed 10 seconds or be below 0.11 seconds (bounds of equation)
            return False
        else:
            return True

    async def vibrate(level, count=1, duration_on=0.65, gap=0.65):  # send vibrate command to Pavlok 2

        if value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
            count = str(count)
            level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
            duration_on = d_calc(duration_on)
            gap = d_calc(gap)
        else:
            raise Exception("Parameter values invalid")

        value = "8" + count + "0c" + level + duration_on + gap  # format into packet to be sent to Pavlok 2
        await client.write_gatt_char(features["Vibe"], bytes.fromhex(value), response=True)


    async def beep(level, count=1, duration_on=0.65, gap=0.65):  # send beep command to Pavlok 2

        if value_check(level, count, duration_on, gap):  # proceed as long as parameters are okay
            count = str(count)
            level = format(level * 10, 'x').zfill(2)  # conver to hex, ensure 2 digit format
            duration_on = d_calc(duration_on)
            gap = d_calc(gap)
        else:
            raise Exception("Parameter values invalid")

        value = "8" + count + "0c" + level + duration_on + gap  # format into packet to be sent to Pavlok 2
        print(value)
        await client.write_gatt_char(features["Beep"], bytes.fromhex(value), response=True)


    async def shock(level,
              count=1):  # send shock command to Pavlok 2, should be noted that my measurements show the shock elicited 0.7 seconds after function call
        # shock lacks duration on and gap parameters as a hardware feature, repeated shock timing should be handled outside of this function

        if value_check(level, count):  # proceed as long as parameters are okay
            svalue = "8" + str(count) + format(level * 10, 'x').zfill(
                2)  # format into packet to be sent to Pavlok 2, ensuring hex, 2 digit format
        else:
            raise Exception("Parameter values invalid")
        await client.write_gatt_char(features["Zap"], bytes.fromhex(svalue), response=True)


    asyncio.run_coroutine_threadsafe(beep(3), loop)


    @route("/", method="POST")
    def index():
        current_health = request.json.get("player", {}).get("state", {}).get("health", 100)
        previous_health = request.json.get("previously", {}).get("player", {}).get("state", {}).get("health", 0)

        print(f"current health: {current_health}")
        print(f"previous health: {previous_health}")

        if current_health == 0:
            if previous_health > current_health:
                if request.json["provider"]["steamid"] == request.json["player"]["steamid"]:
                    asyncio.run_coroutine_threadsafe(shock(3), loop)

        print(request.json)

        return "test"


    run(host='0.0.0.0', port=8080)

    # print("blah")
    #
    # while True:
    #     print("main thread!")
    #     time.sleep(2)
    #
