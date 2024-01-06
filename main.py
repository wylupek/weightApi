from fastapi import FastAPI
import random
import time
from threading import Thread
import signal
import RPi.GPIO as GPIO
import I2C_LCD_driver
from time import *
import sys
from hx711 import HX711


app = FastAPI()


@app.get("/weight")
async def root():
    return {"current_weight": round(random.uniform(0, 1000), 3)}  # grams



def run_scale(print_values=False):
    mylcd = I2C_LCD_driver.lcd()
    mylcd.lcd_display_string("Loading...", 1)

    known_weight_grams = 227
    GPIO.setmode(GPIO.BCM)
    hx = HX711(dout_pin=5, pd_sck_pin=6)

    # check if successful
    if hx.zero():
        raise ValueError('Tare is unsuccessful.')

    x0 = hx.get_data_mean()
    if not x0:
        raise ValueError('Invalid x0: ', x0)

    input('Put known weight on the scale and then press Enter')
    x1 = hx.get_data_mean()
    if not x1:
        raise ValueError('Invalid x1: ', x1)

    if print_values:
        print('x0: ', x0)
        print('x1: ', x1)

    try:
        while True:
            reading = hx.get_data_mean(20)
            ratio1 = reading - x0
            ratio2 = x1 - x0
            ratio = ratio1 / ratio2
            mylcd.lcd_clear()
            mylcd.lcd_display_string("{:.1f}".format(known_weight_grams * ratio) + " g", 1)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()


thread = Thread(target=run_scale(True))
thread.daemon = True
thread.start()
