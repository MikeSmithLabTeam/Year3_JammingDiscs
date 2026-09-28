int xStepPin = 2;
int xDirPin = 3;
int xPower = A2;
int xLimit = 10;

int Speed = 200;
float Pause;

void setup() {
  pinMode(xStepPin, OUTPUT);
  pinMode(xDirPin, OUTPUT);
  pinMode(xPower, OUTPUT);
  pinMode(xLimit, INPUT_PULLUP);
  
  Pause = Speed;
  Pause = 500 / Pause;

  digitalWrite(xPower, HIGH);
  Serial.begin(9600);
  
  // Print help menu on startup
  printHelp();
}

void loop() 
{
  if (Serial.available() > 0) 
  {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim(); // Removes any extra spaces or carriage returns (\r)

    if (cmd.equals("H") || cmd.equals("h")) {
      printHelp();
    }
    else if (cmd.equals("RX")) {
      resetx();
      Serial.println('f');
    }
    else if (cmd.startsWith("MX") && (cmd.endsWith("+") || cmd.endsWith("-"))) {
      // Parse format like MX100+ or MX50-
      char sign = cmd.charAt(cmd.length() - 1);
      String numStr = cmd.substring(2, cmd.length() - 1);
      int steps = numStr.toInt();
      
      // Direction: '+' = false (one way), '-' = true (the other way)
      boolean xdir = (sign == '-'); 
      movestep(xdir, steps);
      Serial.println('f');
    }
    else if (cmd.startsWith("V") || cmd.startsWith("v")) {
      // Parse format like V300
      String numStr = cmd.substring(1);
      int newSpeed = numStr.toInt();
      
      if (newSpeed > 0) {
        Speed = newSpeed;
        Pause = Speed;
        Pause = 500 / Pause; // Recalculate the pause delay
        Serial.print("Speed set to: ");
        Serial.println(Speed);
      } else {
        Serial.println("Invalid speed value.");
      }
      Serial.println('f');
    }
    else if (cmd.length() > 0) {
      Serial.println("Unknown command. Type H for help.");
    }
  }
}

void printHelp() {
  Serial.println("\n========================================");
  Serial.println("        X-AXIS CONTROLLER HELP            ");
  Serial.println("========================================");
  Serial.println(" Commands:");
  Serial.println("    H        - Print this help menu");
  Serial.println("    RX       - Home/Reset X axis using limit switch");
  Serial.println("    MX100+   - Move X positive by specified steps");
  Serial.println("    MX50-    - Move X negative by specified steps");
  Serial.println("    V200     - Set motor speed (steps/sec)");
  Serial.println("========================================\n");
}

void resetx() {
  Serial.println("Homing X axis...");
  digitalWrite(xPower, LOW);
  digitalWrite(xDirPin, true); 
  
  int stepsTaken = 0;
  while (digitalRead(xLimit) == LOW) {
     digitalWrite(xStepPin, HIGH);
     delayMicroseconds(Pause * 1000);
     digitalWrite(xStepPin, LOW);
     delayMicroseconds(Pause * 1000);
     stepsTaken++;
     if (stepsTaken > 10000) { // Safety timeout
       Serial.println("Homing timeout reached!");
       break;
     }
   }
   Serial.println("X Homing Finished!");
   digitalWrite(xPower, HIGH);
}  

void movestep(boolean xdir, int steps) {
  digitalWrite(xPower, LOW);
  digitalWrite(xDirPin, xdir);

  for (int i = 0; i < steps; i++) {
    digitalWrite(xStepPin, HIGH);
    delayMicroseconds(Pause * 1000);
    digitalWrite(xStepPin, LOW);
    delayMicroseconds(Pause * 1000);
  }
  
  digitalWrite(xPower, HIGH);
}
