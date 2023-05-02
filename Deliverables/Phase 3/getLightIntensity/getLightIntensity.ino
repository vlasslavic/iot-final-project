#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Arduino.h>

const char* ssid = "TP-LINK_6BAC";
const char* password = "95706801";
const char* mqtt_server = "192.168.0.159";

WiFiClient vanieriot;
PubSubClient client(vanieriot);
const int pin1 = A0;
int sensorVal;
const int ANALOG_READ_PIN = 36; 
const int RESOLUTION = 12;
long now = millis();
long lastMeasure = 0;

void setup_wifi()
{
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected - ESP-8266 IP address: ");
  Serial.println(WiFi.localIP());
}
void callback(String topic, byte *message, unsigned int length)
{
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messagein;

  for (int i = 0; i < length; i++)
  {
    Serial.print((char)message[i]);
    messagein += (char)message[i];
  }
}
void reconnect()
{
  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("vanieriot"))
    {
      Serial.println("connected");
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 3 seconds");
      // Wait 5 seconds before retrying
      delay(3000);
    }
  }
}
void setup()
{

  Serial.begin(9600);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  pinMode(pin1, INPUT);
}
void loop()
{
  if (!client.connected())
  {
    reconnect();
  }
  if (!client.loop())
    client.connect("vanieriot");

  now = millis();
  if (now - lastMeasure > 5000)
  {
    lastMeasure = now;
    float t = analogRead(pin1);

    static char res[7];
    dtostrf(t, 6, 0, res);
    client.publish("get-light-intensity", res);

    Serial.print("Intensity is: ");
    Serial.print(t);
    Serial.println("");
  }
}
