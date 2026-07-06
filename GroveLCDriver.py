"""
https://files.seeedstudio.com/wiki/Grove_LCD_RGB_Backlight/res/JHD1313%20FP-RGB-1%201.4.pdf
   SDA  -> GPIO 2  pin 3
   SCL  -> GPIO 3  pin 5
   VCC  -> 5V      pin 4
   GND  -> GND     pin 6

  Notes sudo systemctl enable pigpiod
  sudo systemctl start pigpiod
"""
import time
import pigpio

LCD_ADDRESS = 0x3E

#pg17
SCREEN_CLEAR = 0x01
CURSOR_RETURN = 0x02
INPUT_SET = 0x04
DISPLAY_SWITCH = 0x08
FUNCTION_SET = 0x20

LCD_ENTRY_LEFT_I_D = 0x02
LCD_DISPLAY_ON_D = 0x04
LCD_8BITMODE_DL = 0x10
LCD_1LINE_N = 0x00
LCD_5x8DOTS_F = 0x00

LCD_CMD_REG  = 0x80
LCD_DATA_REG = 0x40


class GroveLcd:
    def __init__(self, i2c_bus: int = 1) -> None:
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Cannot connect to pigpiod.")

        self._lcd_h = self._pi.i2c_open(i2c_bus, LCD_ADDRESS)

        self._display_function = LCD_8BITMODE_DL | LCD_1LINE_N | LCD_5x8DOTS_F
        self._display_control = LCD_DISPLAY_ON_D
        self._display_mode = LCD_ENTRY_LEFT_I_D

        self._init_lcd()

    def _send_cmd(self, cmd: int) -> None:
        self._pi.i2c_write_i2c_block_data(self._lcd_h, LCD_CMD_REG, [cmd])

    def _send_data(self, data: int) -> None:
        self._pi.i2c_write_i2c_block_data(self._lcd_h, LCD_DATA_REG, [data])

    def _init_lcd(self) -> None:
        time.sleep(0.05)                                         
        self._send_cmd(FUNCTION_SET | self._display_function) 
        time.sleep(0.005)                                      
        self._send_cmd(FUNCTION_SET | self._display_function)  
        time.sleep(0.005)                                       
        self._send_cmd(FUNCTION_SET | self._display_function)  
        self._send_cmd(DISPLAY_SWITCH | self._display_control)
        self.clear()
        self._send_cmd(INPUT_SET | self._display_mode)

    def clear(self) -> None:
        self._send_cmd(SCREEN_CLEAR)
        time.sleep(0.002)

    def home(self) -> None:
        self._send_cmd(CURSOR_RETURN)
        time.sleep(0.002)

    def write(self, text: str) -> None:
        self.clear()
        self.home()
        for char in text:
            self._send_data(ord(char))

    def close(self) -> None:
        try:
            self._pi.i2c_close(self._lcd_h)
        except Exception:
            pass
        self._pi.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False
