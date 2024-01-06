from fastapi import FastAPI
import random
from threading import Thread
import RPi.GPIO as GPIO
import I2C_LCD_driver
from hx711 import HX711
import time


app = FastAPI()
current_weight = 0


@app.get("/weight")
async def root():
    # return {"current_weight": round(random.uniform(0, 1000), 3)}  # grams
    return {"current_weight": abs(round(current_weight, 1))}


# x values for mass 227g
def run_scale(x0: int = 23, x1: int = 395936,
              print_values: bool = False, calibrate: bool = False) -> None:
    my_lcd = I2C_LCD_driver.lcd()
    my_lcd.lcd_display_string("Loading...", 1)

    known_weight_grams = 227
    GPIO.setmode(GPIO.BCM)
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

    my_lcd.lcd_clear()
    try:
        global current_weight
        previous_weight = 0
        while True:
            reading = hx.get_data_mean(10)
            ratio1 = reading - x0
            ratio2 = x1 - x0
            ratio = ratio1 / ratio2
            previous_weight = current_weight
            current_weight = known_weight_grams * ratio
            if abs(round(current_weight, 1)) != abs(round(previous_weight, 1)):
                my_lcd.lcd_clear()
            my_lcd.lcd_display_string("{:.1f}".format(abs(current_weight)) + " g", 1)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()


thread = Thread(target=run_scale)
thread.daemon = True
thread.start()
