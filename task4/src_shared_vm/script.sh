#!/bin/bash

# Подключение скрипта логирования (определены функции log_info, log_error и т.п.)
source logger.sh

# Пути до старого и нового расположения демонов
OLD_PATH="/opt/misc"
NEW_PATH="/srv/data"
NAME_PATTERN="foobar-daemon"

units=$(systemctl list-unit-files --type=service | cut -d " " -f 1 | grep '^foobar-.*\.service$')


# Проверка запуска от root-пользователя
check_root() {
    if [[ "$EUID" -ne 0 ]]; then
        log_error "Этот скрипт нужно запускать от root."
        exit 1
    fi
}

# Останавливает systemd-сервис
systemctl_stop() {
    local unit="$1"
    log_info "Останавливаем сервис $unit"
    systemctl stop "$unit"

    # Проверка, остановлен ли сервис
    if [[ "$(systemctl is-active "$unit")" == "active" ]]; then
        log_error "Сервис $unit не был остановлен!"
        return 1
    else
        log_success "Сервис $unit остановлен"
    fi
}

# Запускает systemd-сервис
systemctl_start() {
    local unit="$1"
    log_info "Запускаем сервис $unit"
    systemctl start "$unit"

    # Проверка, запущен ли сервис
    if [[ "$(systemctl is-active "$unit")" == "inactive" ]]; then
        log_error "Сервис $unit не был запущен!"
        return 1
    else
        log_success "Сервис $unit запущен"
    fi
}

# Перемещает директорию демона из OLD_PATH в NEW_PATH
move_daemon() {
    local name="$1"
    local src="$OLD_PATH/$name"
    local dest="$NEW_PATH/"

    log_info "Копирование: $src → $dest"
    cp -r "$src" "$dest"
    rm -rf "$src"
}

# Заменяет пути в unit-файле systemd с OLD_PATH на NEW_PATH
replace_unit_paths() {
    local unit_file="$1"
    log_info "Обновляем пути в unit-файле $unit_file"
    sed -i "s|$OLD_PATH|$NEW_PATH|g" "$unit_file"
}

# Перезагружает systemd после изменения unit-файлов
reload_systemd() {
    log_info "Перезагрузка systemd daemon"
    systemctl daemon-reload
}

# Создание или удаление бэкапов демонов и unit-файлов
backup() {
    local date_stamp
    date_stamp=$(date +%Y-%m-%d_%H-%M-%S)
    local backup_daemons="path_daemons.bak.$date_stamp"
    local backup_units="path_units.bak.$date_stamp"
    local daemon_paths
    daemon_paths=$(find "$OLD_PATH" -name "$NAME_PATTERN")

    case "$1" in
        create|"")
            log_info "Создание бэкапов: $backup_daemons и $backup_units"

            # Бэкап директорий демонов
            mkdir -p "$backup_daemons"
            for path in $daemon_paths; do
                local dirname
                dirname=$(basename "$(dirname "$path")")
                mkdir -p "$backup_daemons/$dirname"
                cp -r "$path" "$backup_daemons/$dirname/"
            done
            local unit_files
            unit_files=$(systemctl show -p FragmentPath $units | cut -d= -f2)

            mkdir -p "$backup_units"
            for file in $unit_files; do
                cp "$file" "$backup_units/"
            done
            log_success "Бэкапы созданы"
            ;;
        remove)
            # Удаление всех бэкапов
            log_warn "Удаление всех бэкапов path_daemons.bak.* и path_units.bak.*"
            rm -rf path_daemons.bak.*
            rm -rf path_units.bak.*
            ;;
        *)
            # Обработка неправильных аргументов
            log_error "Использование: backup [create|remove]"
            return 1
            ;;
    esac
}

# Основная логика обработки демонов и их unit-файлов
run() {
    # Получение списка сервисов foobar-*.service
    path_units=$(systemctl show -p FragmentPath $units | cut -d "=" -f 2)

    if [[ -z "$units" ]]; then
        log_error "Не найдены сервисы с именем foobar-*"
        return 1
    fi

    for unit in $units; do
        # Получение пути до unit-файла
        local unit_file
        unit_file=$(systemctl show -p FragmentPath "$unit" | cut -d= -f2)

        if [[ ! -f "$unit_file" ]]; then
            log_warn "Пропущен: unit-файл $unit не найден"
            continue
        fi

        # Извлечение имени демона (например, из foobar-gamma.service → gamma)
        local daemon_name
        daemon_name=${unit#foobar-}
        daemon_name=${daemon_name%.service}

        log
        log_info "Обработка сервиса: $(bold $unit)"

        systemctl_stop "$unit"             # Остановка сервиса
        move_daemon "$daemon_name"         # Перемещение исполняемого файла
        replace_unit_paths "$unit_file"    # Обновление путей в unit-файле
        reload_systemd                     # Перезагрузка systemd
        systemctl_start "$unit"            # Запуск сервиса

        log_success "$unit — завершено"
        log "------------------------"
    done
}

check_log_txt() {
    local found_log
    found_log=$(find "$NEW_PATH" -type f -name "log.txt" -print)

    if [[ -z "$found_log" ]]; then
        log_error "Файлы log.txt не найдены — демоны, возможно, не были запущены!"
    else
        log_success "Файлы log.txt найден — демоны запущены."
        for log in $found_log; do
            log_info $log : "$(head -n 1 "$log")"
        done
    fi
}


# Точка входа
main() {
    check_root         # Проверка прав
    backup create      # Создание бэкапа
    run                # Основной цикл
    check_log_txt      # Проверка запуска демонов
}

# Вызов main
main
