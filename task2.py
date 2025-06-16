import os
import sys
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
import subprocess
from typing import List


class BuildScript:
    """Основной класс для сборки проекта"""
    
    def __init__(self, repo_url: str, src_path: str, version: str):
        """Инициализация параметров сборки"""
        self.repo_url = repo_url      # URL Git-репозитория
        self.src_path = src_path      # Путь к исходникам в репозитории
        self.version = version        # Версия продукта
        self.work_dir = Path("task2") # Рабочая директория
        self.clone_dir = self.work_dir / "clone"  # Директория для клонирования
        self.src_dir = self.work_dir / src_path   # Целевая директория с исходниками
        self.archive_dir = self.work_dir # Директория для архивов
        self.archive_name = self._generate_archive_name()  # Имя архива

    def __str__(self) -> str:
        """Строковое представление конфигурации"""
        return (
            f"Конфигурация сборки:\n"
            f"  URL репозитория: {self.repo_url}\n"
            f"  Путь к исходникам: {self.src_path}/\n"
            f"  Версия: {self.version}\n"
            f"  Рабочая директория: {self.work_dir}/\n"
            f"  Имя архива: {self.archive_name}\n"
            f"  Путь к архиву: {self.archive_dir}/\n"
        )

    def _generate_archive_name(self) -> str:
        """Генерация имени архива на основе последней папки и даты"""
        last_dir = self.src_path.split("/")[-1]  # Последняя папка в пути
        current_date = datetime.now().strftime('%d%m%Y')  # Текущая дата
        return f"{last_dir}{current_date}"

    def _clone_repository(self) -> None:
        """Клонирование Git-репозитория"""
        try:
            # Очистка и создание рабочих директорий
            if self.work_dir.exists():
                shutil.rmtree(self.work_dir)
            self.work_dir.mkdir(parents=True, exist_ok=True)
            
            # Клонирование с минимальной глубиной для экономии времени/места
            subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, str(self.clone_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Репозиторий успешно склонирован в {self.clone_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка клонирования репозитория: {e.stderr}")
            if self.work_dir.exists():
                shutil.rmtree(self.work_dir)
            sys.exit(1)

    def _copy_source_files(self) -> None:
        """Копирование исходных файлов в целевую директорию"""
        try:
            source_path = self.clone_dir / self.src_path
            if not source_path.exists():
                raise FileNotFoundError(f"Путь {source_path} не существует")
            
            shutil.copytree(source_path, self.src_dir, dirs_exist_ok=True)
            print(f"Исходные файлы скопированы в {self.src_dir}")
        except Exception as e:
            print(f"Ошибка копирования файлов: {e}")
            sys.exit(1)

    def _cleanup_clone_directory(self) -> None:
        """Очистка временной директории с репозиторием"""
        try:
            shutil.rmtree(self.clone_dir)
            print(f"Временная директория {self.clone_dir} с репозиторием удалена")
        except Exception as e:
            print(f"Ошибка удаления временной директории {self.clone_dir}: {e}")
            sys.exit(1)

    def _find_source_files(self) -> List[str]:
        """Поиск всех исходных файлов (.py, .js, .sh)"""
        source_files = []
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith((".py", ".js", ".sh")):
                    # Сохраняем относительные пути
                    rel_path = os.path.relpath(os.path.join(root, file), self.src_dir)
                    source_files.append(rel_path)
        return source_files

    def _create_version_file(self) -> None:
        """Создание файла version.json"""
        try:
            version_data = {
                "name": "hello world",
                "version": self.version,
                "files": self._find_source_files()
            }

            version_file = self.src_dir / "version.json"
            with open(version_file, "w") as f:
                json.dump(version_data, f, indent=4)
            print(f"Файл версии создан: {version_file}")
        except Exception as e:
            print(f"Ошибка создания version.json: {e}")
            sys.exit(1)

    def _create_archive(self) -> None:
        """Создание zip-архива с исходниками"""
        try:
            shutil.make_archive(
                base_name=str(self.archive_dir / self.archive_name),
                format="zip",
                root_dir=self.src_dir
            )
            print(f"Архив создан: {self.archive_dir}/{self.archive_name}.zip")
        except Exception as e:
            print(f"Ошибка создания архива: {e}")
            sys.exit(1)

    def run(self) -> None:
        """Основной процесс сборки"""
        print("Начало процесса сборки...")
        self._clone_repository()            # Шаг 1: Клонирование
        self._copy_source_files()           # Шаг 2: Копирование файлов
        self._create_version_file()         # Шаг 3: Создание version.json
        self._cleanup_clone_directory()     # Шаг 4: Очистка
        self._create_archive()              # Шаг 5: Архивирование
        print("Сборка успешно завершена!")


def parse_arguments() -> argparse.Namespace:
    """Разбор аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Скрипт для сборки проекта")
    parser.add_argument(
        "-u", "--repo-url",
        # default="https://github.com/paulbouwer/hello-kubernetes",
        required=True,
        help="URL Git-репозитория"
    )
    parser.add_argument(
        "-p", "--src-path",
        # default="src/app",
        required=True,
        help="Относительный путь к исходному коду в репозитории"
    )
    parser.add_argument(
        "-v", "--version",
        # default="25.3000",
        required=True,
        help="Версия продукта (например, 1.0.0)"
    )
    return parser.parse_args()


def main() -> None:
    """Главная функция выполнения"""
    args = parse_arguments()
    build_script = BuildScript(args.repo_url, args.src_path, args.version)
    print(build_script)  # Вывод конфигурации
    build_script.run()   # Запуск процесса сборки


if __name__ == "__main__":
    main()