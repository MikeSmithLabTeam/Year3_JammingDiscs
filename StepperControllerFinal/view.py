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

    mode_choices = [("Move", 1), ("Bounce", 2), ("Stagger", 3)]

    def __init__(self, root):
        self.root = root
        self.root.title(PROGRAM_NAME)
        self.root.protocol('WM_DELETE_WINDOW', self.on_quit_clicked)
        self.calibrated = tk.BooleanVar()
        
        self.init_gui()
        #self.current_x_position = 0
        #self.current_y_position = 0
        #self.port_status = False

    #### GUI objects ####
    def init_gui(self):
        """Run all methods to create frames and objects"""
        #self.create_top_menu()
        self.create_left_frame()
        self.create_right_frame()
        # frames in left frame
        self.create_serial_port_frame()
        self.create_calibration_frame()
        self.create_control_frame()
        # frames in right frame
        self.create_area_frame()
        self.create_view_frame()
        self.create_edit_frame()
        # objects in left frame's sub-frames
        self.create_serial_port_objects()
        
        self.create_calibration_objects()
        #self.create_control_objects()
        # objects in right frame's sub-frames
        #self.create_area_frame_objects()
        #self.create_view_objects()
        #self.create_edit_objects()

    def create_top_menu(self):
        """Create menu bar and run methods to populate it"""
        self.menu_bar = tk.Menu(self.root)
        self.create_file_menu()
        self.create_mode_menu()
        self.create_help_menu()

    def create_file_menu(self):
        """File submenu to top menu"""
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Quit", command=self.on_quit_clicked)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.root.config(menu=self.menu_bar)

    def create_mode_menu(self):
        """Mode submenu to top menu"""
        self.mode_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.mode_value = tk.IntVar()
        self.mode_value.set(1)
        for txt, val in self.mode_choices:
            self.mode_menu.add_radiobutton(label=txt, variable=self.mode_value,
                                           value=val, command=self.update_mode)
        self.menu_bar.add_cascade(label="Mode", menu=self.mode_menu)
        self.root.config(menu=self.menu_bar)

    def create_help_menu(self):
        """Help submenu to top menu"""
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Controller Tutorial",
                                   command=self.on_tutorial_clicked)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.root.config(menu=self.menu_bar)

    # Left frame and its sub-frames/objects
    def create_left_frame(self):
        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side="left")

    def create_serial_port_frame(self):
        """Frame to contain objects to select the serial port"""
        self.serial_port_frame = tk.Frame(self.left_frame)
        self.serial_port_frame.pack(side='top')

    def create_serial_port_objects(self):
        """Objects to select the serial port"""
        # frame title
        tk.Label(self.serial_port_frame, text='Serial',
                 bg='black', fg='white').pack(side="top", fill='x')
        # Button to find the available ports
        #self.fetch_ports_button = tk.Button(self.serial_port_frame, text='Fetch Ports',
                                            #command=self.fetch_ports_button_clicked)
        #self.fetch_ports_button.pack()
        # Option menu to select serial port
        self.serial_port_options = serial_ports()
        #tk.Label(self.serial_port_frame, text='Select a serial port').pack()
        self.serial_port_choice = tk.StringVar(self.serial_port_frame)
        print(self.serial_port_choice)
        self.serial_port_option_menu = tk.OptionMenu(self.serial_port_frame,
                                                     self.serial_port_choice,
                                                     *self.serial_port_options)
        self.serial_port_option_menu.pack(fill='x')
        # Open the selected port
        tk.Button(self.serial_port_frame, text='Open Port',
                  command=self.open_serial_port).pack()

    def create_calibration_frame(self):
        """Frame to contain objects to calibrate the barriers"""
        self.calibration_frame = tk.Frame(self.left_frame)
        self.calibration_frame.pack(side='top', pady=20)
        tk.Label(self.calibration_frame, text='Calibration',
                 bg='black', fg='white').pack(side="top", fill='x')

    def create_calibration_objects(self):
        """Objects to display positions/areas and calibrate the barriers"""
        # Button to move the barriers to the limit switches
        self.move_to_zero_button = tk.Button(self.calibration_frame,
                                             text='Move to zero',
                                             command = self.move_to_zero_button_clicked)
        self.move_to_zero_button.pack(fill='x')
#        # Labels to display the positions of each barrier, the separation between them and
#        # the area fraction
#        self.current_x_position_string = tk.StringVar()
#        self.current_y_position_string = tk.StringVar()
#        self.current_separation_string = tk.StringVar()
#        self.area_fraction_string = tk.StringVar()
#        tk.Label(self.calibration_frame, text='paddle x pos').pack()
#        tk.Label(self.calibration_frame, textvariable=self.current_x_position_string).pack()
#        tk.Label(self.calibration_frame, text='paddle y pos').pack()
#        tk.Label(self.calibration_frame, textvariable=self.current_y_position_string).pack()
#        tk.Label(self.calibration_frame, text='Paddle separation').pack()
#        tk.Label(self.calibration_frame, textvariable=self.current_separation_string).pack()
#        tk.Label(self.calibration_frame, text='Area Fraction').pack()
#        tk.Label(self.calibration_frame, textvariable=self.area_fraction_string).pack()
#        self.current_x_position_string.set(0)
#        self.current_y_position_string.set(0)
#        self.current_separation_string.set(ZERO_SEPARATION)
#        self.area_fraction_string.set("Not Available")
#        # Checkbutton to confirm that the barriers are at zero
#        self.calibrated.set = False
#        self.calibration_checkbutton = tk.Checkbutton(self.calibration_frame,
#                                                      text='Calibrated?',
#                                                      variable=self.calibrated)
#        self.calibration_checkbutton.pack()

    def create_control_frame(self):
        """Frame to contain objects that control movement of barriers"""
        self.control_frame = tk.Frame(self.left_frame)
        self.control_frame.pack(side='top', pady=20)
        tk.Label(self.control_frame, text='Control', bg='black',
                 fg='white').pack(side="top", fill='x')

    def create_control_objects(self):
        """Objects to control movement of barriers"""
        # Check buttons to decide whether barriers move or not
        self.paddle_x_move = tk.BooleanVar(value=True)
        self.paddle_y_move = tk.BooleanVar(value=True)
        tk.Checkbutton(self.control_frame, text='Move Paddle X',
                       variable=self.paddle_x_move, state='active').pack()
        tk.Checkbutton(self.control_frame, text='Move Paddle Y',
                       variable=self.paddle_y_move, state='active').pack()
        # Radio buttons to decide direction of barriers
        self.paddle_x_in = tk.BooleanVar(value=True)
        self.paddle_y_in = tk.BooleanVar(value=True)
        tk.Radiobutton(self.control_frame, text='Paddle X In',
                       variable=self.paddle_x_in, value=True).pack()
        tk.Radiobutton(self.control_frame, text='Paddle X Out',
                       variable=self.paddle_x_in, value=False).pack()
        tk.Radiobutton(self.control_frame, text='Paddle Y In',
                       variable=self.paddle_y_in, value=True).pack()
        tk.Radiobutton(self.control_frame, text='Paddle Y Out',
                       variable=self.paddle_y_in, value=False).pack()

        # Scale to decide distance barriers move
        self.distance_scale_label = tk.StringVar()
        tk.Label(self.control_frame, textvariable=self.distance_scale_label).pack(anchor='w')
        self.distance_scale_label.set("Distance [mm]")
        self.distance_scale = tk.Scale(self.control_frame, from_=MIN_DISTANCE,
                                       to=MAX_DISTANCE, orient='horizontal')
        self.distance_scale.pack()
        # Scale to decide speed barriers move
        self.speed_scale = tk.Scale(self.control_frame, from_=MIN_SPEED,
                                    to=MAX_SPEED, label='Speed [mm/s]',
                                    orient='horizontal', resolution=0.1)
        self.speed_scale.pack()
        # Scale to decide how many intervals/bounces are made for interval/bounce modes
        self.repeats_scale_label = tk.StringVar()
        tk.Label(self.control_frame, textvariable=self.repeats_scale_label).pack(anchor='w')
        self.repeats_scale_label.set("N/A")
        self.repeats_scale = tk.Scale(self.control_frame, from_=MIN_REPEATS,
                                      to=MAX_REPEATS, orient='horizontal')
        self.repeats_scale.pack()
        # Scale to decide on the length of the pause between intervals in pause mode
        self.pause_scale_label = tk.StringVar()
        tk.Label(self.control_frame, textvariable=self.pause_scale_label).pack(anchor='w')
        self.pause_scale_label.set("N/A")
        self.pause_scale = tk.Scale(self.control_frame, from_=MIN_PAUSE,
                                    to=MAX_PAUSE, orient='horizontal')
        self.pause_scale.pack()
        # Button to start movement using current settings
        self.go_button = tk.Button(self.control_frame, text='Go',
                                  command=self.go_button_clicked)
        self.go_button.pack(fill='x', pady=10)

    # Right frame and its sub-frames/objects
    def create_right_frame(self):
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side="right")

    def create_area_frame(self):
        """Frame to contain objects which works out the area fraction"""
        self.area_frame = tk.Frame(self.right_frame)
        self.area_frame.pack(side='top', fill='x', padx=100)

    def create_area_frame_objects(self):
        """Objects to calculate the area fraction"""
        # Scale for number of particles
        self.particles_scale = tk.Scale(self.area_frame,
                                        from_=0,
                                        to=5000,
                                        label='Number of \n Particles',
                                        orient='horizontal')
        self.particles_scale.pack(side='left')
        # Scale for particle diameters
        self.particle_diameter_scale = tk.Scale(self.area_frame,
                                                from_=0,
                                                to=10,
                                                label='Particle \n Diameter (mm)',
                                                orient='horizontal',
                                                resolution=0.1)
        self.particle_diameter_scale.pack(side='left')
        # Radio buttons for the shape of particle
        self.particle_type = tk.IntVar(value=1)
        tk.Radiobutton(self.area_frame,
                       text='Hexagonal Nut',
                       variable=self.particle_type,
                       value=1).pack()
        tk.Radiobutton(self.area_frame,
                       text='Ball',
                       variable=self.particle_type,
                       value=2).pack()
        # Button the update the area fraction line for these numbers
        tk.Button(self.area_frame,
                  text='Update Graph',
                  command=self.update_area_fraction_graph).pack()

    def create_view_frame(self):
        """ frame to contain the graph displaying movement"""
        self.view_frame = tk.Frame(self.right_frame)
        self.view_frame.pack(side='top')

    def create_view_objects(self):
        """matplotlib figure canvas to contain plot for displaying movement"""
        self.area_figure = plt.figure()
        self.area_figure_axes = self.area_figure.add_axes([.15, .15, .7, .7])
        self.area_figure_axes.plot([],[])
        self.area_figure_axes2 = self.area_figure_axes.twinx()
        self.area_figure_axes2.plot([],[])
        self.figure_canvas = FigureCanvasTkAgg(self.area_figure, master=self.view_frame)
        self.figure_canvas.get_tk_widget().pack()
        self.figure_canvas.show()
        self.toolbar = NavigationToolbar2TkAgg(self.figure_canvas, self.view_frame)
        self.toolbar.update()

    def create_edit_frame(self):
        """frame to contain objects which can save the graph data"""
        self.edit_frame = tk.Frame(self.right_frame)
        self.edit_frame.pack(side='top', fill='x')
        tk.Label(self.edit_frame, text='Edit').pack(side="top", anchor='w')

    def create_edit_objects(self):
        """Objects to save the graph"""
        self.read_button = tk.Button(self.edit_frame, text='Read',
                                     command=self.read_button_clicked)
        self.read_button.pack(side="left")
        self.save_filename_box = tk.Entry(self.edit_frame)
        self.save_filename_box.pack(side="left", padx=10)
        self.save_button = tk.Button(self.edit_frame, text='Save',
                                     command=self.save_button_clicked)
        self.save_button.pack(side="left", padx=10)

    #### Object Callbacks ####
    def on_quit_clicked(self):
        """Method to close the serial port when the Tk window is closed"""
        check = self.open_serial_port()
        if check == True:
            self.port.close()
        sys.exit()

    def on_tutorial_clicked(self):
        """Display help box - need to populate"""
        messagebox.showinfo("Tutorial", "No help yet")

    def go_button_clicked(self):
        """Gathers all the options and generates the serial message to move the barriers"""
        print(ZERO_SEPARATION)
        if self.calibrated.get() == True: # calibrated?
            # get all the movement values
            self.mode = self.mode_value.get()
            print('mode')
            print(self.mode)
            self.distance = self.distance_scale.get()
            print(self.distance_scale.get())
            self.speed = self.speed_scale.get()
            print(self.speed)
            self.repeats = self.repeats_scale.get()
            self.comport = self.serial_port_choice.get()
            self.pause_time = self.pause_scale.get()

            if self.comport: # port open?
                # create serial message based on mode and update graph
                if self.mode_value.get() == 1:
                    self.serial_message = self.generate_move_message()
                    self.update_move_graph()
                elif self.mode_value.get() == 2:
                    self.serial_message = self.generate_bounce_message()
                    self.update_bounce_graph()
                else:
                    self.serial_message = self.generate_stagger_message()
                    self.update_stagger_graph()
                print(self.new_x_position, self.new_y_position)
                print(0<=self.new_x_position<=75 and 0<=self.new_y_position<=75)
                if 0 <= self.new_x_position <= 75 and 0 <= self.new_y_position <= 75: # in bounds?
                    if self.mode_value.get() != 2:
                        # if mode is bounce then readjust the values in the calibration frame
                        self.current_x_position = self.new_x_position
                        self.current_y_position = self.new_y_position
                        self.current_x_position_string.set(self.current_x_position)
                        self.current_y_position_string.set(self.current_y_position)
                        self.current_separation_string.set(ZERO_SEPARATION -
                                                           self.current_x_position -
                                                           self.current_y_position)
                        self.area_fraction_string.set(self.total_particle_area/
                                                      ((ZERO_SEPARATION-self.current_x_position-self.current_y_position)
                                                       *TRAY_HEIGHT))
                    self.send_serial_message()
                else:
                    # show messagebox if trying to move out of bounds
                    messagebox.showinfo(message="Cannot barriers below 0mm or above 75mm")

            else:
                # show messagebox if the port isn't open/selected
                messagebox.showinfo(message="Please select a serial port first")
        else:
            # show messagebox if the port isn't calibrated
            messagebox.showinfo(message="Please move to zero before starting")

    def update_mode(self):
        """Change slider text depending on mode"""
        mode = self.mode_value.get()
        if mode == 1:
            self.repeats_scale_label.set("N/A")
            self.pause_scale_label.set("N/A")
            self.distance_scale_label.set("Distance [mm]")
        elif mode == 2:
            self.repeats_scale_label.set("Bounces")
            self.pause_scale_label.set("N/A")
            self.distance_scale_label.set("Bounce Distance [mm]")
        elif mode == 3:
            self.repeats_scale_label.set("No. of Intervals")
            self.pause_scale_label.set("Pause between intervals")
            self.distance_scale_label.set("Interval Distance")

    def fetch_ports_button_clicked(self):
        """Fetch the list of available serial ports on the PC"""
        self.serial_port_choice.set('')
        self.serial_port_option_menu['menu'].delete(0, 'end')
        self.serial_port_options = serial_ports()
        for option in self.serial_port_options:
            self.serial_port_option_menu['menu'].add_command(label=option,
                                        command=tk._setit(self.serial_port_choice, option))

    def move_to_zero_button_clicked(self):
        """Send the serial commands that will move the barriers to zero and update positions"""
        if self.port_status == True:
            self.port.write(b"<0,1>")
            self.port.write(b"<9,48>")
            
            # self.calibration_checkbutton.toggle()
#            self.current_x_position = 0
#            self.current_y_position = 0
#            self.current_x_position_string.set(self.current_x_position)
#            self.current_y_position_string.set(self.current_y_position)
#            print(self.distance_scale.get())
#            print(self.speed_scale.get())
#            #print(self.mode)
#        else:
#            print("open a serial port")

    def open_serial_port(self):
        """Open the selected serial port"""
        self.port_status = False
        self.comport = self.serial_port_choice.get()
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
        if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
            if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
                message = "<5,{}>".format(steps)
            elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
                message = "<7,{}>".format(steps)
            elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
                message = "<8,{}>".format(steps)
            else:
                message = "<6,{}>".format(steps)
            message_as_byte.append(message.encode())
        elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
            if self.paddle_x_in.get() == True:
                message = "<1,{}>".format(steps)
            elif self.paddle_x_in.get() == False:
                message = "<2,{}>".format(steps)
            message_as_byte.append(message.encode())
        elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
            if self.paddle_y_in.get() == True:
                message = "<3,{}>".format(steps)
            elif self.paddle_y_in.get() == False:
                message = "<4,{}>".format(steps)
            message_as_byte.append(message.encode())
        else:
            print("No Movement Selected")
        return message_as_byte

    def generate_bounce_message(self):
        """Generate the list of serial commands for the bounce mode"""
        message_as_byte = []
        step_speed = self.speed * SPEED_2_STEP_SPEED
        steps = self.distance * DISTANCE_2_STEP
        # Speed
        message = "<9,{}>".format(step_speed)
        message_as_byte.append(message.encode())
        # Bounces
        message = "<10,{}>".format(self.repeats)
        message_as_byte.append(message.encode())
        # Movement
        if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
            if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
                message = "<11,{}>".format(steps)
            elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
                message = "<17,{}>".format(steps)
            elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
                message = "<18,{}>".format(steps)
            else:
                message = "<12,{}>".format(steps)
            message_as_byte.append(message.encode())
        elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
            if self.paddle_x_in.get() == True:
                message = "<14,{}>".format(steps)
            elif self.paddle_x_in.get() == False:
                message = "<15,{}>".format(steps)
            message_as_byte.append(message.encode())
        elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
            if self.paddle_y_in.get() == True:
                message = "<16,{}>".format(steps)
            elif self.paddle_y_in.get() == False:
                message = "<17,{}>".format(steps)
            message_as_byte.append(message.encode())
        else:
            print("No Movement Selected")
        return message_as_byte

    def generate_stagger_message(self):
        """Generate the list of serial commands for the stagger mode"""
        message_as_byte = []
        step_speed = self.speed * SPEED_2_STEP_SPEED
        steps = self.distance * DISTANCE_2_STEP
        # Speed
        message = "<9,{}>".format(step_speed)
        message_as_byte.append(message.encode())
        # Intervals
        message = "<19,{}>".format((self.repeats))
        message_as_byte.append((message.encode()))
        # Interval Pause Time
        message = "<20,{}>".format(self.pause_time)
        message_as_byte.append((message.encode()))
        # Movement
        if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
            if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
                message = "<21,{}>".format(steps)
            elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
                message = "<27,{}>".format(steps)
            elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
                message = "<28,{}>".format(steps)
            else:
                message = "<22,{}>".format(steps)
            message_as_byte.append(message.encode())
        elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
            if self.paddle_x_in.get() == True:
                message = "<23,{}>".format(steps)
            elif self.paddle_x_in.get() == False:
                message = "<24,{}>".format(steps)
            message_as_byte.append(message.encode())
        elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
            if self.paddle_y_in.get() == True:
                message = "<25,{}>".format(steps)
            elif self.paddle_y_in.get() == False:
                message = "<26,{}>".format(steps)
            message_as_byte.append(message.encode())
        else:
            print("No Movement Selected")
        return message_as_byte

    def send_serial_message(self):
        """Send each serial command in the list in turn"""
        for m in self.serial_message:
            print(m)
            self.port.write(m)

    #### Graph Methods ####
    def update_move_graph(self):
        """Update the graph and the positions when the barriers move"""
        self.area_figure_axes.clear()
        self.area_figure_axes2.clear()
        if self.speed != 0 and self.distance != 0: # speed and distance !=0?
            # time array
            t = np.linspace(0, self.distance/self.speed, 100)
            # array for paddle x and y depending on directions and whether they move
            # and update paddle positions
            if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
                if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
                    x = np.linspace(self.current_x_position,
                                    self.current_x_position + self.distance, 100)
                    y = np.linspace(self.current_y_position,
                                    self.current_y_position + self.distance, 100)
                    self.new_x_position = self.current_x_position + self.distance
                    self.new_y_position = self.current_y_position + self.distance
                elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
                    x = np.linspace(self.current_x_position, self.current_x_position + self.distance, 100)
                    y = np.linspace(self.current_y_position, self.current_y_position - self.distance, 100)
                    self.new_x_position = self.current_x_position + self.distance
                    self.new_y_position = self.current_y_position - self.distance
                elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
                    x = np.linspace(self.current_x_position, self.current_x_position - self.distance, 100)
                    y = np.linspace(self.current_y_position, self.current_y_position + self.distance, 100)
                    self.new_x_position = self.current_x_position - self.distance
                    self.new_y_position = self.current_y_position + self.distance
                else:
                    x = np.linspace(self.current_x_position, self.current_x_position - self.distance, 100)
                    y = np.linspace(self.current_y_position, self.current_y_position - self.distance, 100)
                    self.new_x_position = self.current_x_position - self.distance
                    self.new_y_position = self.current_y_position - self.distance
            elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
                if self.paddle_x_in.get() == True:
                    x = np.linspace(0, self.distance, 100)
                    y = np.linspace(0, 0, 100)
                    self.new_x_position = self.current_x_position + self.distance
                elif self.paddle_x_in.get() == False:
                    x = np.linspace(0, -self.distance, 100)
                    y = np.linspace(0, 0, 100)
                    self.new_x_position = self.current_x_position - self.distance
                self.new_y_position = self.current_y_position
            elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
                if self.paddle_y_in.get() == True:
                    x = np.linspace(0, 0, 100)
                    y = np.linspace(0, self.distance, 100)
                    self.new_y_position = self.current_y_position + self.distance
                elif self.paddle_y_in.get() == False:
                    x = np.linspace(0, 0, 100)
                    y = np.linspace(0, -self.distance, 100)
                    self.new_y_position = self.current_y_position - self.distance
                self.new_x_position = self.current_x_position
            else:
                x = np.linspace(0, 0, 100)
                y = np.linspace(0, 0, 100)
                self.new_x_position = self.current_x_position
                self.new_y_position = self.current_y_position
        # No movement set flat lines
        else:
            t = np.linspace(0, 10, 100)
            x = np.linspace(0, 0, 100)
            y = x
            self.new_x_position = self.current_x_position
            self.new_y_position = self.current_y_position
        # update graphs and values in calibration frame
        self.calculate_particle_areas()
        area = self.total_particle_area/((ZERO_SEPARATION-x-y)*TRAY_HEIGHT)
        self.area_figure_axes.plot(t, x, 'b-')
        self.area_figure_axes.plot(t, y, 'r-')
        self.area_figure_axes.legend(['Paddle X', 'Paddle Y'])
        self.area_figure_axes2.plot(t, area, 'g-', )
        self.area_figure_axes.set_xlabel('Time [s]')
        self.area_figure_axes.set_ylabel('Distance [mm]')
        self.area_figure_axes2.set_ylabel('Area Fraction')
        self.area_figure_axes2.legend(['Area Fraction'])
        self.figure_canvas.draw()

    def update_bounce_graph(self):
        """Update the graph and the positions when the barriers bounce"""
        self.area_figure_axes.clear()
        self.area_figure_axes2.clear()
        s = self.speed
        A = (self.distance)
        P = (self.distance/self.speed)
        if self.speed != 0 and self.distance != 0 and self.repeats != 0: # speed and distance !=0?
            # time array
            t = np.linspace(0, (self.distance / self.speed)*2*self.repeats, 1000)
            # array for paddle x and y depending on directions and whether they move
            # and update paddle positions
            if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
                if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
                    self.new_x_position = self.current_x_position + A
                    self.new_y_position = self.current_y_position + A
                    a = s * (P - abs(t % (2 * P)- P))
                    b = s * (P - abs(t % (2 * P) - P))
                elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
                    self.new_x_position = self.current_x_position + A
                    self.new_y_position = self.current_y_position - A
                    a = s * (P - abs(t % (2 * P) - P))
                    b = -s * (P - abs(t % (2 * P) - P))
                elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
                    self.new_x_position = self.current_x_position - A
                    self.new_y_position = self.current_y_position + A
                    a = -s * (P - abs(t % (2 * P) - P))
                    b = s * (P - abs(t % (2 * P) - P))
                else:
                    self.new_x_position = self.current_x_position - A
                    self.new_y_position = self.current_y_position - A
                    a = -s * (P - abs(t % (2 * P) - P))
                    b = -s * (P - abs(t % (2 * P) - P))
            elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
                if self.paddle_x_in.get() == True:
                    self.new_x_position = self.current_x_position + A
                    self.new_y_position = self.current_y_position
                    a = s * (P - abs(t % (2 * P) - P))
                    b = np.linspace(0, 0, 1000)
                elif self.paddle_x_in.get() == False:
                    self.new_x_position = self.current_x_position - A
                    self.new_y_position = self.current_y_position
                    a = -s * (P - abs(t % (2 * P) - P))
                    b = np.linspace(0, 0, 1000)
            elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
                if self.paddle_y_in.get() == True:
                    self.new_x_position = self.current_x_position
                    self.new_y_position = self.current_y_position + A
                    a = np.linspace(0, 0, 1000)
                    b = s * (P - abs(t % (2 * P) - P))
                elif self.paddle_y_in.get() == False:
                    self.new_x_position = self.current_x_position
                    self.new_y_position = self.current_y_position - A
                    a = np.linspace(0, 0, 1000)
                    b = -s * (P - abs(t % (2 * P) - P))
            else:
                self.new_x_position = self.current_x_position
                self.new_y_position = self.current_y_position
                a = np.linspace(0, 0, 1000)
                b = np.linspace(0, 0, 1000)
        # No movement set flat lines
        else:
            self.new_x_position = self.current_x_position
            self.new_y_position = self.current_y_position
            t = np.linspace(0, 10, 1000)
            a = np.linspace(0, 0, 1000)
            b = np.linspace(0, 0, 1000)
        # update graphs and values in calibration frame
        a = a + self.current_x_position
        b = b + self.current_y_position
        self.area_figure_axes.plot(t, a, 'b-')
        self.area_figure_axes.plot(t, b, 'r-')
        plt.xlabel('Time [s]')
        plt.ylabel('Distance [steps]')
        self.area_figure_axes.legend(['Paddle A', 'Paddle B'])
        self.calculate_particle_areas()
        area = self.total_particle_area/((ZERO_SEPARATION - a - b) * TRAY_HEIGHT)
        self.area_figure_axes2.plot(t, area, 'g-')
        plt.xlabel('Time [s]')
        plt.ylabel('Area Fraction')
        self.figure_canvas.draw()

    def update_stagger_graph(self):
        """Update the graph and the positions when the barriers bounce"""
        self.area_figure_axes.clear()
        self.area_figure_axes2.clear()
        speed = self.speed
        intervals = self.repeats # intervals
        dist = self.distance
        pause = self.pause_time
        tmax = (dist/speed)*intervals
        if self.speed != 0 and self.distance != 0 and self.repeats != 0:
            # time array
            t = np.linspace(0, tmax, 100*intervals)
            for i in range(intervals):
                start = 100 * (i + 1)
                end = 100 * (i + 2)
                t[start:end] += (i + 1) * pause
            # array for paddle x and y depending on directions and whether they move
            # and update paddle positions
            if self.paddle_x_move.get() == True and self.paddle_y_move.get() == True:
                if self.paddle_x_in.get() == True and self.paddle_y_in.get() == True:
                    self.new_x_position = self.current_x_position + dist*intervals
                    self.new_y_position = self.current_y_position + dist * intervals
                elif self.paddle_x_in.get() == True and self.paddle_y_in.get() == False:
                    self.new_x_position = self.current_x_position + dist*intervals
                    self.new_y_position = self.current_y_position - dist*intervals
                elif self.paddle_x_in.get() == False and self.paddle_y_in.get() == True:
                    self.new_x_position = self.current_x_position - dist*intervals
                    self.new_y_position = self.current_y_position + dist*intervals
                else:
                    self.new_x_position = self.current_x_position - dist*intervals
                    self.new_y_position = self.current_y_position - dist*intervals
            elif self.paddle_x_move.get() == True and self.paddle_y_move.get() == False:
                if self.paddle_x_in.get() == True:
                    self.new_x_position = self.current_x_position + dist*intervals
                    self.new_y_position = self.current_y_position
                elif self.paddle_x_in.get() == False:
                    self.new_x_position = self.current_x_position - dist*intervals
                    self.new_y_position = self.current_y_position
            elif self.paddle_x_move.get() == False and self.paddle_y_move.get() == True:
                if self.paddle_y_in.get() == True:
                    self.new_x_position = self.current_x_position
                    self.new_y_position = self.current_y_position + dist*intervals
                elif self.paddle_y_in.get() == False:
                    self.new_x_position = self.current_x_position
                    self.new_y_position = self.current_y_position - dist*intervals
            else:
                self.new_x_position = self.current_x_position
                self.new_y_position = self.current_y_position
        # No movement set flat lines
        else:
            t = np.linspace(0, 10, 1000)
            self.new_x_position = self.current_x_position
            self.new_y_position = self.current_y_position
        # update graphs and values in calibration frame
        a = np.linspace(self.current_x_position, self.new_x_position, 100 * intervals)
        b = np.linspace(self.current_x_position, self.new_y_position, 100 * intervals)
        self.area_figure_axes.plot(t, a, 'b-')
        self.area_figure_axes.plot(t, b, 'r-')
        plt.xlabel('Time [s]')
        plt.ylabel('Distance [steps]')
        self.area_figure_axes.legend(['Paddle A', 'Paddle B'])
        self.calculate_particle_areas()
        area = self.total_particle_area/((ZERO_SEPARATION - a - b) * TRAY_HEIGHT)
        self.area_figure_axes2.plot(t, area, 'g-')
        plt.xlabel('Time [s]')
        plt.ylabel('Area Fraction')
        self.figure_canvas.draw()

    def calculate_particle_areas(self):
        """Calculate the total area of all the particles"""
        type = self.particle_type.get()
        diameter = self.particle_diameter_scale.get()
        number = self.particles_scale.get()
        if type == 1: # Nut
            particle_area = 0.5*np.sqrt(3)*(diameter)**2
        elif type == 2: #Ball
            particle_area = np.pi*(diameter/2)**2
        self.total_particle_area = particle_area*number

    def update_area_fraction_graph(self):
        print("update")

    def read_button_clicked(self):
        print("Read Button Clicked")

    def save_button_clicked(self):
        print("Save Button Clicked")


if __name__ == '__main__':
    root = tk.Tk()
    View(root)
    root.mainloop()
