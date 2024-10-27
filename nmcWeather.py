import sys
import os
import json
import requests
import sched
import time

class WeatherApp:
    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        if not os.path.exists('config.json'):
            self.setup_initial_config()
        else:
            self.update_weather()
            self.start_timer()

    def start_timer(self):
        self.scheduler.enter(1800, 1, self.update_weather)  # 每半小时更新一次天气数据
        self.scheduler.run()

    def setup_initial_config(self):
        province = input("请输入省份: ")
        city = input("请输入城市: ")
        stationid = self.get_station_id(province, city)

        config = {
            "province": province,
            "city": city,
            "stationid": stationid
        }
        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
        print("配置已保存。")
        self.update_weather()
        self.start_timer()

    def get_station_id(self, province_name, city_name):
        province_code = self.get_province_code(province_name)
        print(f"Province code for {province_name}: {province_code}")
        if province_code:
            city_code = self.get_city_code(province_code, city_name)
            print(f"City code for {city_name}: {city_code}")
            return city_code
        else:
            print("无法找到省份代码。")
            sys.exit(1)

    def get_province_code(self, province_name):
        url = "http://www.nmc.cn/rest/province"
        response = requests.get(url)
        if response.status_code == 200:
            provinces = response.json()
            for province in provinces:
                if province['name'] == province_name:
                    return province['code']
        return None

    def get_city_code(self, province_code, city_name):
        url = f"http://www.nmc.cn/rest/province/{province_code}"
        response = requests.get(url)
        if response.status_code == 200:
            cities = response.json()
            for city in cities:
                if city['city'] == city_name:
                    return city['code']
        return None

    def update_weather(self):
        config = self.load_config()
        weather_data = self.fetch_weather_data(config["stationid"])
        if weather_data:
            self.display_weather(weather_data)
        else:
            print("Failed to fetch weather data.")
    def load_config(self):
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        return config

    def fetch_weather_data(self, stationid):
        url = f"http://www.nmc.cn/rest/weather?stationid={stationid}"
        response = requests.get(url)
        if response.status_code == 200:
            try:
                weather_data = response.json()
                self.save_weather_data(weather_data, stationid)
                return weather_data
            except json.JSONDecodeError:
                print("Error decoding JSON from response")
                print(response.text)  # 打印原始响应
        else:
            print(f"Failed to fetch weather data: {response.status_code}")
        return None

    def save_weather_data(self, weather_data, stationid):
        now = QDateTime.currentDateTime().toString('yyyyMMdd-HHmmss')
        folder_path = os.path.join(os.path.dirname(sys.executable), 'WeatherJson')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, f"{now}-{stationid}.json")
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(weather_data, file, indent=4, ensure_ascii=False)

    def display_weather(self, weather_data):
        real = weather_data["data"]["real"]
        station = real["station"]
        weather = real["weather"]
        wind = real["wind"]
        air = weather_data["data"]["air"]

        city = station['city']
        temperature = weather['temperature']
        humidity = weather['humidity']
        wind_direct = "无持续风向" if wind['direct'] == "9999" else wind['direct']
        wind_power = wind['power']
        air_quality = air['text']
        rain = weather['rain']
        feelst = weather['feelst']

        # 第一行：城市，温度，湿度，风速风向
        print(f"{city} {temperature}°C 湿度: {humidity}% 风速风向: {wind_direct} {wind_power}")

        # 第二行：空气质量、降水量、体感温度
        print(f"空气质量: {air_quality} 降水量: {rain}mm 体感温度: {feelst}°C")

        # 第三行：预警信息（如果有）
        if "warn" in real and real["warn"]["alert"] != "9999":
            warn = real["warn"]
            alert_text = warn["alert"].split("信号")[0] + "信号"
            print(alert_text)
        # 七日天气预报
        self.display_forecast(weather_data["data"]["tempchart"])

    def display_forecast(self, tempchart):
        today = QDateTime.currentDateTime().toString('yyyy/MM/dd')
        start_index = next((index for (index, d) in enumerate(tempchart) if d["time"] == today), None)
        if start_index is not None:
            # 尝试获取7天到1天的数据
            for days in range(7, 0, -1):
                end_index = start_index + days
                if end_index <= len(tempchart):
                    for i in range(start_index, end_index):
                        day_data = tempchart[i]
                        day_of_week = "今天" if i == start_index else QDateTime.fromString(day_data["time"], 'yyyy/MM/dd').toString('ddd')

                        # 处理9999的情况
                        max_temp = "" if day_data['max_temp'] == "9999" else day_data['max_temp']
                        min_temp = "" if day_data['min_temp'] == "9999" else day_data['min_temp']
                        day_text = "" if day_data['day_text'] == "9999" else day_data['day_text']
                        night_text = "" if day_data['night_text'] == "9999" else day_data['night_text']

                        forecast = f"{day_of_week} "
                        if max_temp:
                            forecast += f"{max_temp}°C/"
                        if min_temp:
                            forecast += f"{min_temp}°C "
                        if day_text:
                            forecast += f"{day_text}/"
                        if night_text:
                            forecast += f"{night_text}"

                        print(forecast)
                    break
        else:
            for i in range(7):
                day_of_week = QDateTime.currentDateTime().addDays(i).toString('ddd')
                print(f"{day_of_week} Err°C/Err°C Err/Err")

if __name__ == "__main__":
    app = WeatherApp()
