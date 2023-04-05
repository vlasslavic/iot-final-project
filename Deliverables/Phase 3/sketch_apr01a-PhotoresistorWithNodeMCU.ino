#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "TP-Link_2AD8";
const char* password = "14730078";
const char* mqtt_server = "192.168.0.196";

const int pResistor = A0; // Photoresistor at Arduino analog pin A0
//const int ledPin = 13;/
//Variables
int value; // Store value from photoresistor (0-1023)
char light[50];
String light_str;

WiFiClient vanieriot;
PubSubClient client(vanieriot);

void setup_wifi() {
 delay(10);
 // We start by connecting to a WiFi network
 Serial.println();
 Serial.print("Connecting to ");
 Serial.println(ssid);
 WiFi.begin(ssid, password);
 while (WiFi.status() != WL_CONNECTED) {
  delay(500);
  Serial.print(".");
 }
 Serial.println("");
 Serial.print("WiFi connected - ESP-8266 IP address: ");
 Serial.println(WiFi.localIP());
}

void callback(String topic, byte* message, unsigned int length) {
 Serial.print("Message arrived on topic: ");
 Serial.print(topic);
 Serial.print(". Message: ");
 String messagein;

 for (int i = 0; i < length; i++) {
  Serial.print((char)message[i]);
  messagein += (char)message[i];
 }

}

void reconnect() {
 while (!client.connected()) {
  Serial.print("Attempting MQTT connection...");
  if (client.connect("vanieriot")) {
    Serial.println("connected");

  } else {
    Serial.print("failed, rc=");
    Serial.print(client.state());
    Serial.println(" try again in 3 seconds");
    // Wait 5 seconds before retrying
    delay(3000);
    }
  }
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  pinMode(pResistor, INPUT); // Set pResistor - A0 pin as an input (optional) 
//  pinMode(ledPin, OUTPUT);/
}

void loop() {
  // put your main code here, to run repeatedly:
  value = analogRead(pResistor);
  if (!client.connected()) {
  reconnect();
  }
  if(!client.loop())
  client.connect("vanieriot");
  light_str = String(value);
  light_str.toCharArray(light, light_str.length() + 1);
  client.publish("light-intensity",light);
//  Serial.println("Light intensity is: ");
//  Serial.println (value);

//  if(value < 500){
//    digitalWrite(ledPin, HIGH);
//  }
//  else{
//    digitalWrite(ledPin, LOW);
//  }
  delay(5000);
}
