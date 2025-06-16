from itertools import product
import re
import sys
import json
import argparse
from typing import List, Dict, Tuple

class VersionAnalyzer:
    def __init__(self, target_version: str, config_path: str):
        """Инициализация анализатора версий"""
        self.target_version = target_version
        self.config_path = config_path
        self.templates = self._load_config()  # Загружаем шаблоны версий
        self.all_versions = self._generate_all_versions()  # Генерируем все варианты
        self.max_length = self._calculate_max_length()  # Вычисляем максимальную длину
        self.normalized_target = self._normalize_version(self.target_version)  # Нормализуем целевую версию

    def __str__(self) -> str:
        """Строковое представление конфигурации"""
        return (
            f"Анализатор версий:\n"
            f"  Целевая версия: {self.target_version}\n"
            f"  Шаблонов загружено: {len(self.templates)}\n"
            f"  Вариантов сгенерировано: {len(self.all_versions)}\n"
        )

    def _load_config(self) -> Dict[str, str]:
        """Загрузка и валидация конфигурационного файла"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Проверяем формат каждого шаблона
            pattern = re.compile(r'^(\d+|\*)(\.(\d+|\*))*$')  # Формат: цифры и * через точки
            for key, value in config.items():
                if not isinstance(value, str) or not pattern.fullmatch(value):
                    raise ValueError(f"Некорректный шаблон {key}: {value}")
            
            return config
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            sys.exit(1)

    def _normalize_version(self, version: str) -> Tuple[int, ...]:
        """Преобразование версии в кортеж чисел фиксированной длины"""
        parts = version.split('.')
        # Конвертируем в числа и дополняем нулями
        return tuple(int(part) for part in parts) + (0,) * (self.max_length - len(parts))

    def _generate_variants(self, template: str) -> List[str]:
        """Генерация всех комбинаций для шаблона"""
        parts = template.split('.')
        stars = [i for i, p in enumerate(parts) if p == '*']  # Позиции звездочек
        
        if not stars:
            return [template]  # Если нет звездочек - возвращаем как есть
        
        # Генерируем все комбинации 0 и 1 для звездочек
        variants = []
        for combo in product((0, 1), repeat=len(stars)):
            new_version = parts.copy()
            for pos, val in zip(stars, combo):
                new_version[pos] = str(val)
            variants.append('.'.join(new_version))
        
        return variants

    def _generate_all_versions(self) -> List[str]:
        """Генерация всех возможных версий для всех шаблонов"""
        return [
            version 
            for template in self.templates.values() 
            for version in self._generate_variants(template)
        ]

    def _calculate_max_length(self) -> int:
        """Вычисление максимального количества компонентов в версии"""
        versions = list(self.templates.values()) + [self.target_version]
        return max(len(v.split('.')) for v in versions)

    def analyze(self):
        """Анализ и сравнение версий"""
        normalized = {v: self._normalize_version(v) for v in self.all_versions}
        
        # Сортировка по нормализованным значениям
        sorted_versions = sorted(self.all_versions, key=lambda v: normalized[v])
        
        # Фильтрация версий старше целевой
        
        older = []
        for v in sorted_versions:
            if normalized[v] < self.normalized_target:
                older.append(v)
            else:
                break

        # Вывод результатов
        print("\nВсе версии (отсортировано):")
        print('\n'.join(f"  {v}" for v in sorted_versions))
        
        print(f"\nВерсии старше {self.target_version}:")
        print('\n'.join(f"  {v}" for v in older) if older else "  Нет устаревших версий")


def main():
    """Точка входа в программу"""
    parser = argparse.ArgumentParser(description='Анализатор версий ПО')
    parser.add_argument('-v', '--version', default="1.2.3", help='Целевая версия')
    parser.add_argument('-c', '--config', default="config.json", help='Файл шаблонов')
    
    args = parser.parse_args()
    analyzer = VersionAnalyzer(args.version, args.config)
    
    print(analyzer)
    analyzer.analyze()


if __name__ == "__main__":
    main()