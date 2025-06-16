import urllib.request
import json
import time
import concurrent.futures
from typing import List, Dict

class TimeSyncClient:
    """Клиент для получения и обработки данных о времени с сервера"""
    
    def __init__(self, url: str, geo_id: int):
        self.url = url
        self.geo_id = geo_id
            
    
    def fetch_raw_data(self) -> str:
        """Выполняет HTTP-запрос и возвращает сырой ответ"""
        with urllib.request.urlopen(self.url) as response:
            return response.read().decode('utf-8')
        
    
    
    def parse_response(self, raw_data: str) -> Dict:
        """Разбирает JSON-ответ и извлекает необходимые поля"""
        data = json.loads(raw_data)
        clock_data = data['clocks'][str(self.geo_id)]
        
        return {
            'time_ms': data['time'],
            'offset_ms': clock_data['offset'],
            'timezone': clock_data['offsetString']
        }

    @staticmethod
    def calculate_human_time(timestamp_ms: int, offset_ms: int) -> str:
        """Преобразует timestamp в читаемый формат с учётом смещения"""
        total_seconds = (timestamp_ms + offset_ms) // 1000
        return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(total_seconds))

    def execute_single(self) -> Dict:
        """Выполняет один запрос и возвращает обработанные данные"""
        t_start = time.time()
        raw_data = self.fetch_raw_data()
        parsed = self.parse_response(raw_data)
        
        server_utc_seconds = parsed['time_ms'] / 1000.0
        return {
            'raw_data': raw_data,
            'human_time': self.calculate_human_time(parsed['time_ms'], parsed['offset_ms']),
            'timezone': parsed['timezone'],
            'delta': server_utc_seconds - t_start
        }

    def execute_parallel(self, num_requests: int) -> List[Dict]:
        """Выполняет параллельные запросы и возвращает результаты"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.execute_single) for _ in range(num_requests)]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"Ошибка при выполнении запроса: {e}")
            
            return results

def print_results(results: List[Dict]):
    """Выводит результаты запросов"""
    for i, result in enumerate(results, 1):
        print(f"\nРезультат запроса #{i}")
        print("Сырой ответ:")
        print(result['raw_data'])
        print("\nВремя и временная зона:")
        print(f"{result['human_time']} {result['timezone']}")
        print(f"Дельта времени: {result['delta']:.6f} сек")
        print("----------------")

def main():
    """Основная логика программы"""
    GEO_ID = 213
    URL = "https://yandex.com/time/sync.json?geo=" + str(GEO_ID)
    NUM_REQUESTS = 5
    
    client = TimeSyncClient(URL, GEO_ID)
    
    print(f"Выполняю {NUM_REQUESTS} параллельных запросов к API Яндекс.Времени")
    start_time = time.time()
    results = client.execute_parallel(NUM_REQUESTS)
    elapsed = time.time() - start_time
    
    print_results(results)
    
    if results:
        deltas = [r['delta'] for r in results]
        avg_delta = sum(deltas) / len(deltas)
        print(f"\nСредняя дельта по {len(deltas)} запросам: {avg_delta:.6f} сек")
        print(f"Общее время выполнения: {elapsed:.2f} сек")

if __name__ == "__main__":
    main()