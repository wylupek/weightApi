from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
from threading import Thread, Lock
import RPi.GPIO as GPIO
import I2C_LCD_driver
from hx711 import HX711
import time

origins = [
    "http://localhost",
    "http://localhost:8000",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_weight = 0.0


@app.get("/weight")
async def root():
    return {"current_weight": abs(round(current_weight, 1))}


def tare_handle(button_pin, my_hx, my_lcd, my_lock):
    pressed = False
    while True:
        if not GPIO.input(button_pin):
            if not pressed:
                my_lock.acquire()
                my_lcd.lcd_display_string("Tare pressed...", 1)
                if my_hx.zero():
                    raise ValueError('Tare is unsuccessful.')
                my_lcd.lcd_clear()
                pressed = True
                my_lock.release()
        else:
            pressed = False


# x values for mass 227g
# 1: x0: int = 23, x1: int = 395936
# 2: x0: int = 10, x1: int = 393500
def run_scale(x0: int = 10, x1: int = 393600,
              print_values: bool = False, calibrate: bool = False) -> None:
    GPIO.setmode(GPIO.BCM)
    tare_btn_pin = 26
    known_weight_grams = 227
    GPIO.setup(tare_btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    lcd = I2C_LCD_driver.lcd()
    lcd.lcd_display_string("Loading...", 1)

    hx = HX711(dout_pin=5, pd_sck_pin=6)
    if hx.zero():
        raise ValueError('Tare is unsuccessful.')

    if calibrate:
        x0 = hx.get_data_mean()
        if not x0:
            raise ValueError('Invalid x0: ', x0)

        input('Put known weight on the scale and then press Enter: ')
        x1 = hx.get_data_mean()
        if not x1:
            raise ValueError('Invalid x1: ', x1)

    if print_values:
        print('x0: ', x0)
        print('x1: ', x1)

    lcd.lcd_clear()
    try:
        global current_weight
        lock = Lock()

        tare_thread = Thread(target=tare_handle, args=(tare_btn_pin, hx, lcd, lock))
        tare_thread.daemon = True
        tare_thread.start()

        while True:
            lock.acquire()
            reading = hx.get_data_mean(10)
            ratio1 = reading - x0
            ratio2 = x1 - x0
            ratio = ratio1 / ratio2

            previous_weight = current_weight
            current_weight = known_weight_grams * ratio

            if round(current_weight, 1) != round(previous_weight, 1):
                lcd.lcd_clear()

            if int(current_weight) == 0:
                lcd.lcd_display_string("0.0 g", 1)
            else:
                lcd.lcd_display_string("{:.1f}".format(current_weight) + " g", 1)
            lock.release()
            time.sleep(0.001)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()


thread = Thread(target=run_scale)
thread.daemon = True
thread.start()
