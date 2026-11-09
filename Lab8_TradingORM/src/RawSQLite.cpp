#include "RawSQLite.h"
#include <sqlite3.h>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
namespace {
void check(int rc, sqlite3* db) {
    if (rc != SQLITE_OK && rc != SQLITE_DONE && rc != SQLITE_ROW)
        throw std::runtime_error(sqlite3_errmsg(db));
}
using Statement = std::unique_ptr<sqlite3_stmt, decltype(&sqlite3_finalize)>;
}
void runRawSqliteComparison(const char* filename) {
    sqlite3* handle = nullptr;
    if (sqlite3_open(filename, &handle) != SQLITE_OK) {
        std::string msg = handle ? sqlite3_errmsg(handle) : "Cannot open database";
        if (handle) sqlite3_close(handle);
        throw std::runtime_error(msg);
    }
    std::unique_ptr<sqlite3, decltype(&sqlite3_close)> db(handle, sqlite3_close);
    check(sqlite3_exec(db.get(), "CREATE TABLE IF NOT EXISTS RawTraders (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, level TEXT NOT NULL)", nullptr, nullptr, nullptr), db.get());
    sqlite3_stmt* p = nullptr;
    check(sqlite3_prepare_v2(db.get(), "INSERT INTO RawTraders(name,email,level) VALUES(?,?,?)", -1, &p, nullptr), db.get());
    Statement insert(p, sqlite3_finalize);
    check(sqlite3_bind_text(insert.get(), 1, "Raw demo trader", -1, SQLITE_STATIC), db.get());
    check(sqlite3_bind_text(insert.get(), 2, "raw@example.test", -1, SQLITE_STATIC), db.get());
    check(sqlite3_bind_text(insert.get(), 3, "basic", -1, SQLITE_STATIC), db.get());
    check(sqlite3_step(insert.get()), db.get());
    auto id = sqlite3_last_insert_rowid(db.get());
    sqlite3_stmt* s = nullptr;
    check(sqlite3_prepare_v2(db.get(), "SELECT id,name,email,level FROM RawTraders WHERE id=?", -1, &s, nullptr), db.get());
    Statement select(s, sqlite3_finalize);
    check(sqlite3_bind_int64(select.get(), 1, id), db.get());
    int rc = sqlite3_step(select.get());
    check(rc, db.get());
    if (rc == SQLITE_ROW) {
        std::cout << "SQLite C API: id=" << sqlite3_column_int64(select.get(),0)
            << ", name=" << reinterpret_cast<const char*>(sqlite3_column_text(select.get(),1)) << '\n';
    }
}