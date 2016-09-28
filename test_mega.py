void setup()
{
  Serial.begin(9600);
}

void loop()
{
  Serial.println("Hello Pi");
  if (Serial.available())
  {
   	Serial.println(Serial.read())
	Serial.write(chr('\x06')); #send ACK
	if((chr(Serial.read())) == 'ACK') #received ACK
		Serial.write(chr('\x06')) #send ACK
  }
  delay(1000);
}