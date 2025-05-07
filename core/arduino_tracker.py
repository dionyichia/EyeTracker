import time
import sys
import serial

class ArduinoTracker:
    """Handles connection and communication with Arduino hardware."""
    
    def __init__(self, auto_connect=True, baud_rate=115200, on_detect_callback=None, port_identifiers=['arduino', 'uno']):
        """Initialize the Arduino tracker.
        
        Args:
            auto_connect: If True, try to auto-connect to Arduino
            baud_rate: Baud rate for serial communication
            on_detect_callback: Callback function called when multiple ports are detected
                                Function signature: callback(ports) -> selected_port
        """
        self.arduino = None
        self.baud_rate = baud_rate
        self.port_identifiers = port_identifiers

        
        # If auto_connect is enabled, try to connect automatically
        if auto_connect:
            self.try_connect(on_detect_callback)
    
    def try_connect(self, on_detect_callback=None):
        """Try to connect to Arduino, handling port detection and selection.
        
        Args:
            on_detect_callback: Callback function for port selection
            
        Returns:
            tuple: (success, message)
        """
        ports = self.detect_arduino_ports()

        print("ports ", ports)
        
        if not ports:
            return False, "No Arduino devices detected"
        
        if len(ports) == 1:
            # Only one port found, connect automatically
            port = ports[0]['port']
            print("here 0")
            success = self.connect_to_arduino(port, self.baud_rate)
            print("here 1 ", success)
            
            if success:
                return True, f"Connected to Arduino at {port}"
            else:
                return False, f"Failed to connect to Arduino at {port}"
        else:
            # Multiple ports found, let user select
            if on_detect_callback:
                selected_port = on_detect_callback(ports)
                if selected_port:
                    success = self.connect_to_arduino(selected_port, self.baud_rate)
                    if success:
                        return True, f"Connected to Arduino at {selected_port}"
                    else:
                        return False, f"Failed to connect to Arduino at {selected_port}"
                else:
                    return False, "No port selected"
            else:
                return False, "Multiple Arduino devices detected, but no selection callback provided"

    # Find availiable ports
    def detect_arduino_ports(self):
        """Detect available Arduino serial ports.
        
        Returns:
            list: List of potential Arduino serial ports
        """
        import serial.tools.list_ports
        
        arduino_ports = []
        
        port_info_list = list(serial.tools.list_ports.comports())
        print("port_info_list:", port_info_list)

        for port_info in port_info_list:
            port_device = port_info.device  # Example: '/dev/cu.usbserial-130'
            port_description = port_info.description.lower()  # Example: 'usb serial device'
            print("port_description :",port_description)
            
            if any(identifier in port_description for identifier in self.port_identifiers):
                arduino_ports.append({
                    'port': port_device,
                    'description': port_info.description
                })
        
        return arduino_ports


    # Connect to Arduino
    def connect_to_arduino(self, port, baud_rate):
        try:
            self.arduino = serial.Serial(port, baud_rate)
            return self.arduino
        except serial.SerialException as e:
            print(f"Unable to connect to port: {e}")
            sys.exit(1)

    def is_connected(self):
        """Check if Arduino is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.arduino is not None and self.arduino.is_open
    
    def disconnect(self):
        """Disconnect from Arduino."""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            self.arduino = None

    def readtime(self, cur_time):
        click_time = time.time() - cur_time   
        return click_time

    def check_connection(self, arduino):
        try:
            time.sleep(2)
            arduino = self.connect_to_arduino('/dev/cu.usbserial-A50285BI', 115200)

            arduino.write(("PING\n").encode('utf-8'))
            time.sleep(1)  # Wait a moment for Arduino to process

            ##remve line 39 .inwaiting check what outputs in serail ////////////////////////////////////

            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                if response == "PONG":
                    print("Arduino is connected and responding.")
                    return True
                else:
                    print(f"Unexpected response from Arduino: {response}catch\n")
                    return False
            else:
                print("No response from Arduino.")
                return False

        except serial.SerialException as e:
            print(f"Error while checking connection: {e}")
            return False

    def buzzer(self, arduino, command, prev_command):
        # Check if the Arduino is properly connected before sending commands
        #if not check_connection(port, baudrate):
            #print("Failed to communicate with Arduino. Check the connection.")
            #return
        
        #time.sleep(1)
        #arduino = connect_to_arduino(port, baudrate)

        # Send the command if connection check passes

        print(f"Sending command: {command}")
        if command in ['H', 'L']:
            if command != prev_command:
                try:
                    if command == 'H':
                        arduino.write(('H').encode('utf-8'))  # Send the command to Arduino
                    else:
                        arduino.write(('L').encode('utf-8'))  # Send the command to Arduino 
                    arduino.flush() 

                    # Wait for acknowledgment
                    start_time = time.time()
                    while time.time() - start_time < 1:  # 1 second timeout
                        if arduino.in_waiting > 0:
                            response = arduino.readline().decode('utf-8').strip()
                            if response == 'O':
                                print(f"Command '{command}' acknowledged by Arduino.")
                                return 1
                            else:
                                print(f"Response: '{response}' by Arduino.")
                                return 2
                        
                    print(f"No acknowledgment received for command '{command}'.")
                    return 0
                except serial.SerialException as e:
                    print(f"Error sending command: {e}")
                    return 0
            else:
                return 1
        else:
            print("Invalid input. Please enter HIGH or LOW.")
            return 0

if __name__ == "__main__":
    # Establish a single connection to Arduino
    arduino_port = '/dev/cu.usbserial-130'  # Change this to the correct port
    baud_rate = 115200
    tracker = ArduinoTracker()

    time.sleep(2)
    arduino = tracker.connect_to_arduino(arduino_port, baud_rate)
    # Connect to Arduino
    if arduino is None:
        print("Failed to connect to Arduino.\n")

    if not tracker.check_connection(arduino_port, baud_rate):
        print("Arduino is not responding. Exiting.")

    while True:
        if (arduino.in_waiting > 0):
            response = arduino.readline().decode('utf').strip('\n')
            print(response)
        else:
            print("No msg from Arduino.")

        command = input("Enter HIGH/LOW: ").strip().upper()
        if command == "HIGH" or command == "LOW":
            if command == "HIGH":
                arduino.write(('H').encode('utf-8'))  # Send the command to Arduino
            else:
                arduino.write(('L').encode('utf-8'))  # Send the command to Arduino
            print("Interfacing from main")
        elif command == "EXIT":
            break
        else:
            print("Invalid input. Please enter HIGH, LOW, or EXIT.")

    arduino.close()

    """

    """
    """
    # Now continuously check the button state while waiting for the timing window
    start_time = time.time()
    print("Click the button between 1 and 3 seconds into the runtime.")

    click_time = []
    while True:
        button_pressed = read_button_state()
        if button_pressed:
            click_time.append(readtime(start_time))
        
        if(readtime(start_time) >= 5):
            break

    
    if 1 <= click_time[0] <= 3:
        print("Passed, Result:", click_time)
    else:
        print("Fail, Result:", click_time)

    """


    """
    Arduino code: Clicker Button to Video Timing
    // declare pins
    const int button_pin = 4;

    // variable for button state
    int button_state;

    void setup() { // put your setup code here, to run once:
      pinMode(button_pin,INPUT);  // set button pin as input
      Serial.begin(9600);
    }

    void loop() { // put your main code here, to run repeatedly:
      button_state = digitalRead(button_pin);  // read button state
      if(button_state == HIGH){           // if button is pushed
        Serial.println("ON");
      }
      else{                               // if button is not pushed
        Serial.println("OFF");
      }
    }

    """

    """
    Arduino Code: Button to 4 LEDs
    // declare pins
    const int button_pin = 7;
    const int led1 = 3;
    const int led2 = 4;
    const int led3 = 5;
    const int led4 = 6;

    // variable for button state
    int button_state;
    int led1_state;
    int led2_state;
    int led3_state;
    int led4_state;
    int counter;

    void setup() { // put your setup code here, to run once:
      pinMode(button_pin,INPUT);  // set button pin as input
      pinMode(led1, OUTPUT);
      pinMode(led2, OUTPUT);
      pinMode(led3, OUTPUT);
      pinMode(led4, OUTPUT);
        Serial.begin(9600);
    }

    void loop() { // put your main code here, to run repeatedly:
      button_state = digitalRead(button_pin);  // read button state
      if(button_state == HIGH){           // if button is pushed
        Serial.println("ON");
        digitalWrite(led1, HIGH);
        delay(100);
        digitalWrite(led1, LOW);
        delay(100);
        digitalWrite (led2, HIGH);
        delay(100);
        digitalWrite (led2, LOW);
        delay(100);
        digitalWrite (led3, HIGH);
        delay(100);
        digitalWrite (led3, LOW);
        delay(100);
        digitalWrite (led4, HIGH);
        delay(100);
        digitalWrite (led4, LOW);
      }
      else{                               // if button is not pushed
        Serial.println("OFF");
        digitalWrite (led1, LOW);    
        digitalWrite (led2, LOW);
        digitalWrite (led3, LOW);
        digitalWrite (led4, LOW);
      }
    }

    """