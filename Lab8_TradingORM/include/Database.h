#pragma once
#include <string>
#include <sqlite_orm/sqlite_orm.h>
#include "Models.h"
inline auto createStorage(const std::string& filename) {
    using namespace sqlite_orm;
    return make_storage(filename,
        make_table("Traders",
            make_column("id", &Trader::id, primary_key().autoincrement()),
            make_column("name", &Trader::name, not_null()),
            make_column("email", &Trader::email, not_null(), unique()),
            make_column("level", &Trader::level, not_null())),
        make_table("Orders",
            make_column("id", &Order::id, primary_key().autoincrement()),
            make_column("trader_id", &Order::traderId, not_null()),
            make_column("symbol", &Order::symbol, not_null()),
            make_column("side", &Order::side, not_null()),
            make_column("quantity", &Order::quantity, not_null()),
            make_column("price", &Order::price, not_null()),
            make_column("status", &Order::status, not_null()),
            foreign_key(&Order::traderId).references(&Trader::id)));
}
using Storage = decltype(createStorage(""));