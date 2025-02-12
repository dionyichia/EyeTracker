#include <Servo.h>

const int servo1 = 9;       // first servo
const int servo2 = 10;      // second servo
const int button_pin = 3;
const int laser_pin = 5;
const int buzzer_pin = 6;
const int led_pin = 12;

const int point_duration = 5000; // wait time before shifting to next point
const int laser_duration = 2000; // duration for laser to be turned on
const int PRE_FIRE_DELAY = 500;    // 0.5 second delay before firing
const int buzzer_duration = 1000; // Buzzer duration in milliseconds
const unsigned long DEBOUNCE_DELAY = 50; 
//const int blinker_interval = 300;

int button_state = HIGH;
int last_button_state = HIGH;

int laser_state = LOW; // If laser_state is high means the laser is already firing
int laser_flag = LOW; // if laser_flag is high means the laser is suppoesd to be fired

int buzzer_state = LOW;
int led_state = LOW;

int point_tracker = 0; // Initialize point_tracker to 0

unsigned long timestamp = 0;
unsigned long buzzer_start_time = 0; // Timestamp to track buzzer timing
unsigned long laser_start_time = 0; // Timestamp to track laser timing
//unsigned long blink_timestamp = 0; // Timestamp to track laser blinking

Servo myservo1;  // create servo object to control a servo
Servo myservo2;  // create servo object to control a servo

// Set coordinates of laser points (4), (1), (2), (3); (Y-axis, X-axis)
int myPoints[4][2] = {{75, 10}, {70, 60}, {20, 60}, {30, 15}}; 

// Count the number of laser points
int numPoints = sizeof(myPoints) / sizeof(myPoints[0]); 
char click_tracker[4];

int click_counter = -1;
unsigned long last_debounce_time = 0;

void setup() {
  Serial.begin(115200);

  pinMode(button_pin, INPUT_PULLUP);
  pinMode(laser_pin, OUTPUT);
  pinMode(buzzer_pin, OUTPUT);
  pinMode(led_pin, OUTPUT);
  digitalWrite(buzzer_pin, buzzer_state);

  // Attach servos
  myservo1.attach(servo1, 600, 2000);  // Attach the servo
  myservo2.attach(servo2, 600, 2000);  // Attach the servo

  // Initialize timestamp
  timestamp = millis();

  // Zero click tracker array
  for (int i = 0; i < numPoints; i++) {
    click_tracker[i] = '0';
  }
}

void loop() {
  // Check current time and duration
  unsigned long current_time = millis(); 
  unsigned long duration = current_time - timestamp; 
  unsigned long blinker_interval_tracker;
  //Serial.println("current_time,timestamp,duration");
  //Serial.println(current_time);
  //Serial.println(timestamp);
  //Serial.println(duration);

  // Inverse logic, if 1 means button not pressed, 0 means button pressed
  int reading = digitalRead(button_pin);
  //Serial.println(reading);

  if (reading != last_button_state) {
    last_debounce_time = current_time;
    last_button_state = reading;
    //Serial.println(reading);
  }

  if (duration > point_duration) {
    // If laser is still on turn it off before moing
    if (laser_state == HIGH){
      digitalWrite(laser_pin, LOW);
      laser_state = LOW;
    }

    // Update point_tracker to the next point
    point_tracker = (point_tracker + 1) % numPoints;
    //Serial.println("point_tracker");
    //Serial.println(point_tracker);

    int x = myPoints[point_tracker][0];
    int y = myPoints[point_tracker][1];

    // Move the servos
    myservo2.write(x);  // Move the second servo to x position
    myservo1.write(y);  // Move the first servo to y position
  
    // Detach servos
    //myservo1.detach();  // Attach the servo
    //myservo2.detach();  // Attach the servo

    // Set up laser firing
    laser_flag = HIGH;
    laser_start_time = current_time;  // Initialize the start time
    laser_state = LOW;  // Ensure laser starts from OFF state

    // Update timestamp
    timestamp = current_time;
    click_counter++;
  }

  // If laser is OFF and button is pressed, debounce click, turn on buzzer,
  if ((current_time - last_debounce_time) > DEBOUNCE_DELAY) {
    if (reading != button_state) {
      button_state = reading;
    
      if (button_state == LOW) {
        if (laser_state == LOW) {
          Serial.println("Wrong press turn on buzzer");
          digitalWrite(buzzer_pin, HIGH);
          buzzer_state = HIGH;
          buzzer_start_time = current_time;
        } 

        // If laser is ON and button is pressed, turn off laser
        else {
          // Turn off laser
          Serial.println("laser off");
          digitalWrite(laser_pin, LOW);
          laser_state = LOW;
          laser_flag = LOW;
          

          // if (click_counter > 0) {  // Only decrement if positive
          // click_counter--;
          // }

          // Add click to click tracker
          click_tracker[click_counter] = '1';
        }

      } 
    }
  }
  
  // Communicate with Python Script
  if (Serial.available() > 0) {
      // Clear the input buffer first
      while (Serial.available()) {
        char command = Serial.read();
        Serial.println(command);
        
        if (command == 'H') {
          // digitalWrite(buzzer_pin, HIGH);       
          // buzzer_state = HIGH;
          // buzzer_start_time = current_time;
          // laser_state = HIGH;
          // Serial.println('O');

          digitalWrite(led_pin, HIGH);  
          led_state = HIGH;
          
        } else if (command == 'L') {
          // digitalWrite(buzzer_pin, LOW);  
          // buzzer_state = LOW;
          // laser_state = LOW;
          // Serial.println('O');

          digitalWrite(led_pin, LOW);  
          led_state = LOW;
        }
      }
  }

  // laser control logic
  if (laser_flag == HIGH) {
      if (laser_state == LOW) {
          if (current_time - laser_start_time >= PRE_FIRE_DELAY) {
              digitalWrite(laser_pin, HIGH);
              laser_state = HIGH;
              laser_start_time = current_time;  // Reset start time for duration tracking
              Serial.println("on laser");
          }
      }
      else if (current_time - laser_start_time >= laser_duration) {
          // Turn off laser after duration
          digitalWrite(laser_pin, LOW);
          laser_state = LOW;
          laser_flag = LOW;
          Serial.println("off laser");
      }
  }

  if (buzzer_state == HIGH) {    
    if (current_time - buzzer_start_time >= buzzer_duration) {
        digitalWrite(buzzer_pin, LOW);  // Turn off the buzzer
        buzzer_state = LOW;
        digitalWrite(led_pin, LOW);  // Turn off the LED
        led_state = LOW;
    }
  }
  else {                              
      digitalWrite(buzzer_pin, LOW);
      buzzer_state = LOW;
      digitalWrite(led_pin, LOW);  // Turn off the LED
      led_state = LOW;
  }

  //  To end the program
  if(current_time > 20000) {
    //Send counter back to python script
    Serial.println(click_counter);  // Send counter value
    Serial.println(click_tracker);  // Send counter value
    while(1) {} // Actually stop the program
  }

}


// Testing Blink the laser if button is not pressed after 3 seconds of laser firing
  //else if ((button_state == LOW) && (laser_state == HIGH) && (duration > 3000)) {
    //if (current_time - blink_timestamp >= blink_interval) {
      // Toggle laser state for blinking
      //laser_state = !laser_state;
      //digitalWrite(laser_pin, laser_state);
      //blink_timestamp = current_time; // Update blink timestamp
    //}
  //}
