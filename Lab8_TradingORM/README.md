# TradingORM — лабораторна робота №8, варіант 15

C++20, SQLite, sqlite_orm, Repository. Предметна область: трейдери та біржові заявки.

## Складання у Windows (Visual Studio + vcpkg)

Встановіть C++ Desktop Development, CMake і vcpkg. Задайте шлях до свого vcpkg:

```powershell
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake"
cmake --build build --config Release
.\build\Release\TradingORM.exe
```

У разі використання генератора Ninja виконуваний файл може бути у `build/TradingORM.exe`.
Перший запуск у manifest-режимі завантажить бібліотеки, зазначені у vcpkg.json.

Програма при кожному запуску видаляє **лише власні демонстраційні файли** trading_demo.db і raw_demo.db у поточному каталозі, відтворює 5 трейдерів та 15 заявок, демонструє CRUD, JOIN, групування, COMMIT, ROLLBACK і часткове збереження без транзакції. Не зберігайте в цих файлах потрібні дані.

**Увага:** збірка з бібліотекою sqlite_orm у цьому середовищі не перевірялася; запускайте у налаштованому Windows + vcpkg середовищі.