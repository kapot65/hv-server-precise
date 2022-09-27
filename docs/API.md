### API сервера
Ниже перечислены возможные входные команды:
1. Задание напряжения в Вольтах:
   ```json
   {
     "type": "command",
     "command_type": "set_voltage",
     "block": 1,
     "voltage": 1000
   }
   ```
   Поле `voltage` задает желаемое напряжение в Вольтах.

   ---
   **NOTE**

   Здесь и далее во всех командах полe `block` всегда имеет значение 1. Сейчас оно не актуально и осталось в API только в целях обратной совместимости.

   ---
2. Задание напряжения в Вольтах с ожиданием выставления:
   ```json
   {
     "type": "command",
     "command_type": "set_voltage_and_check",
     "block": 1,
     "voltage": 1000,
     "max_error": 1.0,
     "timeout": 20
   }
   ```
   Поля `max_error` и `timeout` задают максимальное отклонение в Вольтах и таймаут в секундах соответственно.

Возможные ответы от сервера:
1. Команда `set_voltage` выполнена успешно:
   ```json
   {
     "type": "answer",
     "answer_type": "set_voltage",
     "block": 1,
     "status": "ok"
   }
   ```
2. Команда `set_voltage_and_check` выполнена успешно:
   ```json
   {
     "type": "answer",
     "answer_type": "set_voltage_and_check",
     "block": 1,
     "voltage": 1000.5,
     "error": 0.5,
     "status": "ok"
   }
   ```
   Поля `voltage` и `error` содержат текущее напряжение и ошибку выставления в Вольтах соответственно.
3. Команда `set_voltage_and_check` завершена по таймауту:
   ```json
   {
     "type": "answer",
     "answer_type": "set_voltage_and_check",
     "block": 1,
     "voltage": 1005.5,
     "error": 5.5,
     "status": "timeout"
   }
   ```
   Поле `voltage` задает желаемое напряжение в Вольтах.
4. Текущее измерение с вольтметра:
   ```json
   {
     "type": "answer",
     "answer_type": "get_voltage",
     "block": 1,
     "voltage": 1000.5,
   }
   ```
   Поле `voltage` содержит текущее напряжение в Вольтах.
5. Ошибка: сервер уже обрабатывает команду:
   ```json
   {
     "type": "reply",
     "reply_type": "error",
     "error_code": 8,
     "error_text_code": "SERVER_BUSY_ERROR",
     "description": "HV server is busy",
   }
6. Ошибка: некорректная команда (не соответствует [JSON-Schema](../commands.schema.json)):
   ```json
   {
     "type": "reply",
     "reply_type": "error",
     "error_code": 9,
     "error_text_code": "INCORRECT_MESSAGE_PARAMS",
     "description": "...",
   }
7. Ошибка обработки алгоритма (в процессе выполнения функции возникло исключение):
   ```json
   {
     "type": "reply",
     "reply_type": "error",
     "error_code": 5,
     "error_text_code": "ALGORITM_ERROR",
     "description": "...",
   }
   ```
