# HV-Server-Precise
Сервер для управления высоковольтной стойкой с помощью БП Fluke 5502E и мультиметров Agilent 34401A (по GPIB). Подробнее см. [PREPRINT.md](./docs/PREPRINT.md)


## Синхронизация с БД
Осуществляется с помощью rclone

Требования:
1. rclone должен быть в PATH
2. сервер должен быть зарегистрирован в rclone.conf
   ```toml
   [numass]
    type = sftp
    host = 192.168.111.1
    shell_type = unix
   ```
3. на сервер должен установлен ssh-ключ для доступа без пароля

Команда синхронизации задается через `DB_SYNC_COMMAND` в [config.py](./config.py)