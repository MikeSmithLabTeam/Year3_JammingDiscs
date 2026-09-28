int dirPinX = 3;
int stepPinX = 2;

int dirPinY = 7;
int stepPinY = 6;

int powerPinX = A2;
int powerPinY = A0;

int Speed = 50;
float Pause;

boolean newData = false;
const byte numChars = 64;
char receivedChars[numChars];
char tempChars[numChars];  

int Setting = 0;
unsigned int Modifier = 0;

void setup() {
  pinMode(dirPinX, OUTPUT);
  pinMode(dirPinY, OUTPUT);
  pinMode(stepPinX, OUTPUT);
  pinMode(stepPinY, OUTPUT);
  pinMode(powerPinX, OUTPUT);
  pinMode(powerPinY, OUTPUT);
  Pause = Speed;
  Pause = 500/Pause;
  digitalWrite(powerPinX, HIGH);
  digitalWrite(powerPinY, HIGH);

  Serial.begin(9600);
  Serial.println("Expects 2 pieces of data - Setting # and Modifier");
  Serial.println("Enter data in this style <13, 1000>  ");
  Serial.println();  
}

void step(boolean dir, unsigned int steps, float Pause) {
  digitalWrite(powerPinX, LOW);
  digitalWrite(powerPinY, LOW);
  digitalWrite(dirPinY, dir);
  if (dir==true) {
  digitalWrite(dirPinX, false);  
  }
  if (dir==false) {
    digitalWrite(dirPinX, true);
  }
  for (int i=0;i<steps;i++) {
    digitalWrite(stepPinX, HIGH);
//    digitalWrite(stepPinY, HIGH);
    delayMicroseconds(Pause*1000);
    digitalWrite(stepPinX, LOW);
//    digitalWrite(stepPinY, LOW);
    delayMicroseconds(Pause*1000);
  }
  digitalWrite(powerPinX, HIGH);
  digitalWrite(powerPinY, HIGH);
}



void loop() {
  recvWithStartEndMarkers();
    
  if (newData == true) {
    strcpy(tempChars, receivedChars);
       // this temporary copy is necessary to protect the original data
    parseData();
    //showParsedData();
    newData = false;

    if (Setting ==1) {             //CCW
      step(true, Modifier, Pause);
    }
    else if (Setting==2) {          //CW
      step(false, Modifier, Pause);
    }
  }
}

void recvWithStartEndMarkers() {  
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else {
        receivedChars[ndx] = '\0'; //terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }

    else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

//==========================

void parseData() {      // split the data into its parts

    char * strtokIndx; // this is used by strtok() as an index

    strtokIndx = strtok(tempChars,",");      
    Setting = atoi(strtokIndx);
 
    strtokIndx = strtok(NULL, ","); 
    Modifier = atoi(strtokIndx);  
}

//============================

void showParsedData() {
    Serial.print("Setting: ");
    Serial.println(Setting);
    Serial.print("Modifier: ");
    Serial.println(Modifier);
}
