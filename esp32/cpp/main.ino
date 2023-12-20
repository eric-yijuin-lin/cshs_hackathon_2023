//https://youtu.be/ghTtpUTSc4o
//安裝程式庫及版本:1.Adafruit SSD1306(2.4.6版)、2.Adafruit GFX(1.10.12版)、3.MAX30105(不限)、4.ESP32Servo(不限版本)
//特別注意，檢查Adafruit BusIO的版本是否為1.7.5版本，否則編譯會出錯

#include "MAX30105.h"           //MAX3010x library
#include "heartRate.h"          //Heart rate calculating algorithm
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

MAX30105 particleSensor;
//計算心跳用變數
const byte RATE_SIZE = 4; //多少平均數量
byte rates[RATE_SIZE]; //心跳陣列
byte rateSpot = 0;
long lastBeat = 0; //Time at which the last beat occurred
float beatsPerMinute;
int beatAvg;

//計算血氧用變數
double avered = 0;
double aveir = 0;
double sumirrms = 0;
double sumredrms = 0;

double SpO2 = 0;
double ESpO2 = 90.0;//初始值
double FSpO2 = 0.7; //filter factor for estimated SpO2
double frate = 0.95; //low pass filter for IR/red LED value to eliminate AC component
int i = 0;
int Num = 30;//取樣30次才計算1次


#include <OneWire.h>
#include <DallasTemperature.h>

#define FINGER_ON 7000    //紅外線最小量（判斷手指有沒有上）
#define MINIMUM_SPO2 90.0 //血氧最小量

const char* ssid = "iPhone-YJL"; //輸入wifi ssid
const char* password = "12345678"; //輸入wifi 密碼WiFi.begin(ssid, password);
const char* userId = "debug-user";
const char* serverUrl = " http://172.20.10.9:9002/health-data";

const int oneWireBus = 17;     
OneWire oneWire(oneWireBus);
DallasTemperature tempSensor(&oneWire);
float temperatureC = 0.0;

TaskHandle_t heartSignTask;
TaskHandle_t temperatureTask;

void setup() {
  Serial.begin(115200);
  connectWifi();
  while(1) {
    testHttp();
    delay(30000);
  }
  initHeartSignSensor();
  initTemperatureSensor();
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.print("STAIP address: ");
  Serial.println(WiFi.localIP());  
}

void testHttp() {
  sendVitalSigns("debug-user", 80, 99.6, 35.7);
}

void initHeartSignSensor() {
  //檢查
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) //Use default I2C port, 400kHz speed
  {
    while(1) {
      Serial.println("找不到MAX30102");
      delay(1000);
    }
  }

  // 設定心跳、血氧測量參數
  byte ledBrightness = 0x7F; //亮度建議=127, Options: 0=Off to 255=50mA
  byte sampleAverage = 4; //Options: 1, 2, 4, 8, 16, 32
  byte ledMode = 2; //Options: 1 = Red only(心跳), 2 = Red + IR(血氧)
  int sampleRate = 800; //Options: 50, 100, 200, 400, 800, 1000, 1600, 3200
  int pulseWidth = 215; //Options: 69, 118, 215, 411
  int adcRange = 16384; //Options: 2048, 4096, 8192, 16384

  // Set up the wanted parameters
  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange); //Configure sensor with these settings
  particleSensor.enableDIETEMPRDY();
  particleSensor.setPulseAmplitudeRed(0x0A); //Turn Red LED to low to indicate sensor is running
  particleSensor.setPulseAmplitudeGreen(0); //Turn off Green LED
  
  // 建立心跳、血氧測量執行緒
  xTaskCreatePinnedToCore(
                    measureHeartSign,   /* Task function. */
                    "measureHeart",     /* name of task. */
                    10000,       /* Stack size of task */
                    NULL,        /* parameter of the task */
                    1,           /* priority of the task */
                    &heartSignTask,      /* Task handle to keep track of created task */
                    0);          /* pin task to core 0 */                  
  delay(500); 
}

void initTemperatureSensor() {
  tempSensor.begin();
  xTaskCreatePinnedToCore(
                    measureTemperature,   /* Task function. */
                    "measureTemp",     /* name of task. */
                    10000,       /* Stack size of task */
                    NULL,        /* parameter of the task */
                    1,           /* priority of the task */
                    &temperatureTask,      /* Task handle to keep track of created task */
                    0);          /* pin task to core 0 */                  
  delay(500); 
}

void measureHeartSign(void * pvParameters ) {
  while(1) {
    long irValue = particleSensor.getIR();    //Reading the IR value it will permit us to know if there's a finger on the sensor or not
    //是否有放手指
    if (irValue > FINGER_ON ) {
      
      //檢查是否有心跳，測量心跳
      if (checkForBeat(irValue) == true) {
        long delta = millis() - lastBeat;//計算心跳差
        lastBeat = millis();
        beatsPerMinute = 60 / (delta / 1000.0);//計算平均心跳
        if (beatsPerMinute < 255 && beatsPerMinute > 20) {
          //心跳必須再20-255之間
          rates[rateSpot++] = (byte)beatsPerMinute; //儲存心跳數值陣列
          rateSpot %= RATE_SIZE;
          beatAvg = 0;//計算平均值
          for (byte x = 0 ; x < RATE_SIZE ; x++) beatAvg += rates[x];
          beatAvg /= RATE_SIZE;
        }
      }

      //測量血氧
      uint32_t ir, red ;
      double fred, fir;
      particleSensor.check(); //Check the sensor, read up to 3 samples
      if (particleSensor.available()) {
        i++;
        ir = particleSensor.getFIFOIR(); //讀取紅外線
        red = particleSensor.getFIFORed(); //讀取紅光
        //Serial.println("red=" + String(red) + ",IR=" + String(ir) + ",i=" + String(i));
        fir = (double)ir;//轉double
        fred = (double)red;//轉double
        aveir = aveir * frate + (double)ir * (1.0 - frate); //average IR level by low pass filter
        avered = avered * frate + (double)red * (1.0 - frate);//average red level by low pass filter
        sumirrms += (fir - aveir) * (fir - aveir);//square sum of alternate component of IR level
        sumredrms += (fred - avered) * (fred - avered); //square sum of alternate component of red level

        if ((i % Num) == 0) {
          double R = (sqrt(sumirrms) / aveir) / (sqrt(sumredrms) / avered);
          SpO2 = -23.3 * (R - 0.4) + 100;
          ESpO2 = FSpO2 * ESpO2 + (1.0 - FSpO2) * SpO2;//low pass filter
          if (ESpO2 <= MINIMUM_SPO2) ESpO2 = MINIMUM_SPO2; //indicator for finger detached
          if (ESpO2 > 100) ESpO2 = 99.9;
          //Serial.print(",SPO2="); Serial.println(ESpO2);
          sumredrms = 0.0; sumirrms = 0.0; SpO2 = 0;
          i = 0;
        }
        particleSensor.nextSample(); //We're finished with this sample so move to next sample
      }
    }
    else {//沒偵測到手指，清除所有數據及螢幕內容顯示"Finger Please"
      //清除心跳數據
      for (byte rx = 0 ; rx < RATE_SIZE ; rx++) rates[rx] = 0;
      beatAvg = 0; rateSpot = 0; lastBeat = 0;
      //清除血氧數據
      avered = 0; aveir = 0; sumirrms = 0; sumredrms = 0;
      SpO2 = 0; ESpO2 = 90.0;
    }
  }
}

void measureTemperature(void * pvParameters) {
  while (1) {
    tempSensor.requestTemperatures(); 
    temperatureC = tempSensor.getTempCByIndex(0);
    Serial.print(temperatureC);
    Serial.println("ºC");
    delay(5000);
  }
}

void sendVitalSigns(char* userId, int heartBeat, double bloodOxygen, float temperatureC) {
  WiFiClientSecure *client = new WiFiClientSecure;
  if(client) {
    client->setInsecure();
    HTTPClient https;

    Serial.println("[HTTPS] begin...");
    if (https.begin(*client, "https://goattl.tw/cshs/line_bot/hello")) {  // HTTPS
      Serial.print("[HTTPS] GET...\n");
      int httpCode = https.GET();
      if (httpCode > 0) {
       Serial.printf("[HTTPS] GET... code: %d\n", httpCode);
        if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_MOVED_PERMANENTLY) {
          String payload = https.getString();
          Serial.println(payload);
        }
      }
      else {
        Serial.printf("[HTTPS] GET... failed, error: %s\n", https.errorToString(httpCode).c_str());
      }
      https.end();
    }
  }
  else {
    Serial.printf("[HTTPS] Unable to connect\n");
  }
  Serial.println();
  Serial.println("Waiting 2min before the next round...");
  delay(10000);
}

String getQueryString(char* userId, int heartBeat, double bloodOxygen, float temperatureC) {
  return String(serverUrl) 
    + "?uid=" + String(userId)
    + "&hb=" + String(heartBeat)
    + "&bo=" + String(bloodOxygen)
    + "&bt=" + String(temperatureC);
}

void loop() {
    //將數據顯示到序列
    Serial.print("Bpm:" + String(beatAvg));
    Serial.println(",SPO2:" + String(ESpO2));
    Serial.print(temperatureC);
    Serial.println("ºC");
    delay(1000);
}

