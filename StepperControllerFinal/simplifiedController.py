import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from configuration import *
import sys
import glob
import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from scipy import signal


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system

        https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class View:

    def __init__(self,root):
        self.root = root
        
        self.root.title(PROGRAM_NAME)
        self.root.protocol('WM_DELETE_WINDOW', self.on_quit_clicked)
        self.calibrated = tk.BooleanVar()
        self.create_serial_port_objects()
        
        self.calibrated = tk.BooleanVar()
        self.go_button_clicked()
        #self.create_control_objects()
        self.current_x_position = 0
        self.current_y_position = 0
        self.port_status = False

    def create_serial_port_objects(self):
        """Objects to select the serial port"""
        # frame title
        self.serial_port_options = serial_ports()
        self.serial_port_choice = self.serial_port_options[0]
        self.open_serial_port()
        self.move_to_zero_button_clicked()
        #self.go_button_clicked()    
    
    
    def open_serial_port(self):
        """Open the selected serial port"""
        #self.port_status = False
        self.comport = self.serial_port_choice
        print(self.comport)
        if self.comport:
            self.port = serial.Serial()
            self.port.port = self.comport
            self.port.baudrate = 9600
            self.port.timeout = 0
            if self.port.isOpen() == False:
                self.port.open()
            self.port_status = True
        else:
            print("Select a COMPORT")
        return self.port_status
    
  
    def move_to_zero_button_clicked(self):
        """Send the serial commands that will move the barriers to zero and update positions"""
        
        if self.port.isOpen() == True:
            print('test')    
            self.port.write(b"<0,1>")
            self.port.write(b"<9,48>")
            self.current_x_position = 0
            self.current_y_position = 0
            
        else:
            print("open a serial port")
    
    
    def create_control_objects(self):
        """Objects to control movement of barriers"""
        # Check buttons to decide whether barriers move or not
        self.paddle_x_move = tk.BooleanVar(value=True)
        self.paddle_y_move = tk.BooleanVar(value=True)
#        tk.Checkbutton(self.control_frame, text='Move Paddle X',
#                       variable=self.paddle_x_move, state='active').pack()
#        tk.Checkbutton(self.control_frame, text='Move Paddle Y',
#                       variable=self.paddle_y_move, state='active').pack()
#        # Radio buttons to decide direction of barriers
#        self.paddle_x_in = tk.BooleanVar(value=True)
#        self.paddle_y_in = tk.BooleanVar(value=True)
#        tk.Radiobutton(self.control_frame, text='Paddle X In',
#                       variable=self.paddle_x_in, value=True).pack()
#        tk.Radiobutton(self.control_frame, text='Paddle X Out',
#                       variable=self.paddle_x_in, value=False).pack()
#        tk.Radiobutton(self.control_frame, text='Paddle Y In',
#                       variable=self.paddle_y_in, value=True).pack()
#        tk.Radiobutton(self.control_frame, text='Paddle Y Out',
#                       variable=self.paddle_y_in, value=False).pack()

        # Scale to decide distance barriers move
        self.distance_scale_label = tk.StringVar()
        #tk.Label(self.control_frame, textvariable=self.distance_scale_label).pack(anchor='w')
        #self.distance_scale_label.set("Distance [mm]")
        self.distance_scale = tk.Scale(self.control_frame, from_=MIN_DISTANCE,
                                       to=MAX_DISTANCE, orient='horizontal')
        #self.distance_scale.pack()
        # Scale to decide speed barriers move
        self.speed_scale = tk.Scale(self.control_frame, from_=MIN_SPEED,
                                    to=MAX_SPEED, label='Speed [mm/s]',
                                    orient='horizontal', resolution=0.1)
        #self.speed_scale.pack()
        # Scale to decide how many intervals/bounces are made for interval/bounce modes
        self.repeats_scale_label = tk.StringVar()
        #tk.Label(self.control_frame, textvariable=self.repeats_scale_label).pack(anchor='w')
        #self.repeats_scale_label.set("N/A")
        #self.repeats_scale = tk.Scale(self.control_frame, from_=MIN_REPEATS,
        #                              to=MAX_REPEATS, orient='horizontal')
        #self.repeats_scale.pack()
        # Scale to decide on the length of the pause between intervals in pause mode
        self.pause_scale_label = tk.StringVar()
        tk.Label(self.control_frame, textvariable=self.pause_scale_label).pack(anchor='w')
        self.pause_scale_label.set("N/A")
        self.pause_scale = tk.Scale(self.control_frame, from_=MIN_PAUSE,
                                    to=MAX_PAUSE, orient='horizontal')
        self.pause_scale.pack()
        # Button to start movement using current settings
        self.go_button_clicked()
        #self.go_button.pack(fill='x', pady=10)
  
    
    
    def on_quit_clicked(self):
        """Method to close the serial port when the Tk window is closed"""
        check = self.open_serial_port()
        if check == True:
            self.port.close()
        sys.exit()

    
    def go_button_clicked(self):
        """Gathers all the options and generates the serial message to move the barriers"""
        #print(ZERO_SEPARATION)
        if True:#self.calibrated.get() == True: # calibrated?
            # get all the movement values
            #self.mode = self.mode_value.get()
            self.distance = 0#self.distance_scale.get()
            self.speed = 0.3#self.speed_scale.get()
            self.repeats = 1#self.repeats_scale.get()
            self.pause_time = 2

            if self.port.isOpen(): # port open?
                # create serial message based on mode and update graph
                self.serial_message = self.generate_move_message()
                    
                #if 0 <= self.new_x_position <= 75 and 0 <= self.new_y_position <= 75: # in bounds?
                    # if mode is bounce then readjust the values in the calibration frame
                self.current_x_position = 5
                self.current_y_position = 5
                    #self.current_x_position_string.set(self.current_x_position)
                    #self.current_y_position_string.set(self.current_y_position)
                    #self.current_separation_string.set(ZERO_SEPARATION -
                                                           #self.current_x_position -
                                                           #self.current_y_position)
                    #self.area_fraction_string.set(self.total_particle_area/
                                                      #((ZERO_SEPARATION-self.current_x_position-self.current_y_position)
                                                       #*TRAY_HEIGHT))
                self.send_serial_message()
            else:
                    # show messagebox if trying to move out of bounds
                    messagebox.showinfo(message="Cannot barriers below 0mm or above 75mm")
        else:
                # show messagebox if the port isn't open/selected
                messagebox.showinfo(message="Please select a serial port first")
        
    
  

    

  
    #### Serial methods ####
    def generate_move_message(self):
        """Generate the list of serial commands for the move mode"""
        message_as_byte = []
        step_speed = self.speed * SPEED_2_STEP_SPEED
        steps = self.distance * DISTANCE_2_STEP
        # Speed
        message = "<9,{}>".format(step_speed)
        message_as_byte.append(message.encode())
        # Movement
        message = "<5,{}>".format(steps)
#        if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
#            if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
#                
#            elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
#                message = "<7,{}>".format(steps)
#            elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
#                message = "<8,{}>".format(steps)
#            else:
#                message = "<6,{}>".format(steps)
#            message_as_byte.append(message.encode())
#        elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
#            if self.paddle_x_in.get() == True:
#                message = "<1,{}>".format(steps)
#            elif self.paddle_x_in.get() == False:
#                message = "<2,{}>".format(steps)
#            message_as_byte.append(message.encode())
#        elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
#            if self.paddle_y_in.get() == True:
#                message = "<3,{}>".format(steps)
#            elif self.paddle_y_in.get() == False:
#                message = "<4,{}>".format(steps)
#            message_as_byte.append(message.encode())
#        else:
#            print("No Movement Selected")
        return message_as_byte


    def send_serial_message(self):
        """Send each serial command in the list in turn"""
        for m in self.serial_message:
            print(m)
            self.port.write(m)

   


if __name__ == '__main__':
    root = tk.Tk()
    a = View(root)
    root.mainloop()
