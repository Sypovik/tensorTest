
target=

# Имя виртуальной машины
VM_NAME=vm

# Пути внутри виртуальной машины
VM_DAEMONS_OLD_PATH=/opt/misc
VM_DAEMONS_NEW_PATH=/srv/data
VM_SRC_PATH=/home/ubuntu/src
VM_UNITS_PATH=/etc/systemd/system

# Пути на хосте
HOST_DAEMONS_OLD_PATH=./deamons_shared_vm/misc
HOST_DAEMONS_NEW_PATH=./deamons_shared_vm/data
HOST_SRC_PATH=./src_shared_vm
HOST_UNITS_PATH=./units
HOST_DAEMONS_PATH=./daemons

# Имена сервисов и unit-файлов
SERVICES=$(shell ls $(HOST_UNITS_PATH) | cut -d "." -f 1)
UNIT_FILES=$(shell ls $(HOST_UNITS_PATH))

.PHONY: launch mount transfer test create clean bash stop restart full_restart

# Запуск новой виртуальной машины
launch:
	multipass launch --name $(VM_NAME) --memory 512M --disk 5G

# Монтирование директорий с хоста в виртуальную машину
mount:
	multipass mount $(HOST_DAEMONS_OLD_PATH) $(VM_NAME):$(VM_DAEMONS_OLD_PATH)
	multipass mount $(HOST_DAEMONS_NEW_PATH) $(VM_NAME):$(VM_DAEMONS_NEW_PATH)
	multipass mount $(HOST_SRC_PATH) $(VM_NAME):$(VM_SRC_PATH)

mkdir:
	multipass exec $(VM_NAME) -- sudo mkdir -p $(VM_DAEMONS_OLD_PATH)
	multipass exec $(VM_NAME) -- sudo mkdir -p $(VM_DAEMONS_NEW_PATH)
	multipass exec $(VM_NAME) -- mkdir -p $(VM_SRC_PATH)

# Копирование unit-файлов в виртуальную машину
transfer:
	multipass exec $(VM_NAME) -- mkdir -p $(VM_SRC_PATH)/tmp

	# Передача unit-файлов
	multipass transfer $(HOST_UNITS_PATH)/* $(VM_NAME):$(VM_SRC_PATH)/tmp
	multipass exec $(VM_NAME) -- sudo sh -c "cp -r $(VM_SRC_PATH)/tmp/* $(VM_UNITS_PATH)"
	multipass exec $(VM_NAME) -- sudo sh -c "rm -rf $(VM_SRC_PATH)/tmp/*"

	# Передача демонов
	multipass transfer -r $(HOST_DAEMONS_PATH)/* $(VM_NAME):$(VM_SRC_PATH)/tmp

	# Копируем содержимое ./daemons/* в /opt/misc
	multipass exec $(VM_NAME) -- sudo sh -c "cp -r $(VM_SRC_PATH)/tmp/* $(VM_DAEMONS_OLD_PATH)"

	# Делаем все foobar-daemon исполняемыми
	multipass exec $(VM_NAME) -- sudo sh -c "chmod +x $(VM_DAEMONS_OLD_PATH)/*/foobar-daemon"

	# Очищаем временный каталог
	multipass exec $(VM_NAME) -- sudo rm -rf $(VM_SRC_PATH)/tmp
	
	multipass transfer $(HOST_SRC_PATH)/*.sh $(VM_NAME):$(VM_SRC_PATH)

# Вывод информации о сервисах
info:
	@echo ""
	@echo "Запущенные сервисы:"
	@multipass exec $(VM_NAME) -- sudo systemctl list-unit-files $(UNIT_FILES)
	@echo "Пути к unit-файлам:"
	@multipass exec $(VM_NAME) -- sudo systemctl show -p FragmentPath $(UNIT_FILES)
	@echo ""

# Создание и настройка виртуальной машины (полный процесс)

create_mount: launch mkdir mount transfer
	

create: mkdir $(target) transfer

	# Перезагружаем systemd и запускаем сервисы
	multipass exec $(VM_NAME) -- sudo systemctl daemon-reexec
	multipass exec $(VM_NAME) -- sudo systemctl daemon-reload
	multipass exec $(VM_NAME) -- sudo systemctl enable $(SERVICES)
	multipass exec $(VM_NAME) -- sudo systemctl start $(SERVICES)
	@$(MAKE) info  # Выводим информацию о сервисах

# Удаление виртуальной машины
clean:
	multipass delete $(VM_NAME)
	multipass purge
	rm -rf $(HOST_DAEMONS_OLD_PATH)/*
	rm -rf $(HOST_DAEMONS_NEW_PATH)/*
	rm -rf $(HOST_SRC_PATH)/*.bak.*

# Вход в виртуальную машину через bash
bash:
	multipass exec $(VM_NAME) -- bash -c 'cd $(VM_SRC_PATH) && bash'

# Остановка виртуальной машины
stop:
	multipass stop $(VM_NAME)

# Перезагрузка виртуальной машины
restart:
	multipass restart $(VM_NAME)

# Полная перезагрузка (остановка + удаление + создание заново)
full_restart: stop clean create