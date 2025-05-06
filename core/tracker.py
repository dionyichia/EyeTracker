import time
import sys
import serial

class ArduinoTracker():

    # Connect to Arduino
    def connect_to_arduino(self, port, baud_rate):
        try:
            arduino = serial.Serial(port, baud_rate)
            return arduino
        except serial.SerialException as e:
            print(f"Unable to connect to port: {e}")
            sys.exit(1)
        
    def read_button_state(self):
        # Read data from Arduino
        button_state = arduino.readline().decode().strip()

        # Process button state
        if button_state == 'ON':
            print("Button is pressed")

            return True
        elif button_state == '0FF':
            print("Button is not pressed")
            return False

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