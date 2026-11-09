#include "TraderRepository.h"
#include "OrderService.h"
#include "RawSQLite.h"
#include <sqlite3.h>
#include <sqlite_orm/sqlite_orm.h>
#include <cstdio>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

void seed(Storage& db, ITraderRepository& repo, OrderService& orders) {
    const std::vector<Trader> traders = {
        {0,"Anna Kovalenko","anna@example.test","pro"},
        {0,"Bohdan Melnyk","bohdan@example.test","basic"},
        {0,"Iryna Shevchenko","iryna@example.test","pro"},
        {0,"Maksym Bondar","maksym@example.test","basic"},
        {0,"Olena Tkachenko","olena@example.test","vip"}
    };
    const std::vector<std::string> symbols = {"AAPL","MSFT","TSLA","NVDA","AMZN"};
    for (int i=0; i<5; ++i) {
        int traderId = repo.add(traders[i]);
        for (int j=0; j<3; ++j) {
            orders.add({0,traderId,symbols[(i+j)%5],j%2==0?"BUY":"SELL",
                       (j+1)*10, 100.0+i*20+j*5, j==2?"filled":"open"});
        }
    }
}
void runQueries(Storage& db) {
    using namespace sqlite_orm;
    std::cout << "\nFILTER: pro traders\n";
    for(const auto& t : db.get_all<Trader>(where(c(&Trader::level)=="pro")))
        std::cout << t.id << " " << t.name << '\n';
    std::cout << "\nSORT + LIMIT (top 3 by name):\n";
    for(const auto& t : db.get_all<Trader>(order_by(&Trader::name),limit(3)))
        std::cout << t.name << '\n';
    std::cout << "\nCOUNT orders: " << db.count<Order>() << '\n';
    auto totals = db.select(columns(&Order::traderId, sum(&Order::quantity)),
                            group_by(&Order::traderId));
    std::cout << "\nGROUP BY trader / total quantity:\n";
    for(const auto& [traderId, total] : totals)
        std::cout << traderId << " / " << (total ? *total : 0) << '\n';
    auto joined = db.select(columns(&Trader::name,&Order::symbol,&Order::side,&Order::quantity),
                  inner_join<Order>(on(c(&Trader::id)==&Order::traderId)),
                  order_by(&Order::id));
    std::cout << "\nJOIN trader and orders:\n";
    for (const auto& [name,symbol,side,qty] : joined)
        std::cout << name << " | " << symbol << " " << side << " " << qty << '\n';
}
void runTransactions(Storage& db) {
    int beforeTraders = db.count<Trader>();
    int beforeOrders = db.count<Order>();
    bool committed = db.transaction([&] {
        int id = db.insert(Trader{0,"Commit Trader","commit@example.test","basic"});
        db.insert(Order{0,id,"AAPL","BUY",8,125.0,"open"});
        return true;
    });
    std::cout << "\nCOMMIT=" << committed << " traders " << beforeTraders << "->" << db.count<Trader>()
              << " orders " << beforeOrders << "->" << db.count<Order>() << '\n';
    beforeTraders = db.count<Trader>(); beforeOrders = db.count<Order>();
    try {
        db.transaction([&] {
            db.insert(Trader{0,"Rollback Trader","rollback@example.test","basic"});
            db.insert(Order{0,-999999,"TSLA","BUY",2,200.0,"open"});
            return true;
        });
        throw std::runtime_error("Expected FK violation did not occur");
    } catch(const std::exception& ex) {
        std::cout << "ROLLBACK caught: " << ex.what() << '\n';
    }
    std::cout << "ROLLBACK traders " << beforeTraders << "->" << db.count<Trader>()
              << " orders " << beforeOrders << "->" << db.count<Order>() << '\n';
    // No explicit transaction: first INSERT remains after the second fails.
    beforeTraders = db.count<Trader>(); beforeOrders = db.count<Order>();
    db.insert(Trader{0,"Partial Trader","partial@example.test","basic"});
    try {
        db.insert(Order{0,-999999,"TSLA","BUY",2,200.0,"open"});
    } catch(const std::exception& ex) {
        std::cout << "WITHOUT TRANSACTION second step failed: " << ex.what() << '\n';
    }
    std::cout << "WITHOUT TRANSACTION traders " << beforeTraders << "->" << db.count<Trader>()
              << " orders " << beforeOrders << "->" << db.count<Order>() << '\n';
}
int main() {
    try {
        // Recreate only demonstration databases, leaving user data elsewhere untouched.
        std::remove("trading_demo.db");
        std::remove("raw_demo.db");
        runRawSqliteComparison("raw_demo.db");
        auto db = createStorage("trading_demo.db");
        db.sync_schema();
        // Enable FK checking on the actual ORM connection (PRAGMA is connection-local).
        db.on_open = [](sqlite3* connection) {
            if (sqlite3_exec(connection,"PRAGMA foreign_keys = ON",nullptr,nullptr,nullptr)!=SQLITE_OK)
                throw std::runtime_error("Could not enable foreign keys");
        };
        SQLiteTraderRepository concrete(db);
        ITraderRepository& repo = concrete;
        OrderService orders(db);
        seed(db,repo,orders);
        std::cout << "Seed: traders=" << db.count<Trader>() << " orders=" << db.count<Order>() << '\n';
        int id = repo.add({0,"CRUD Trader","crud@example.test","basic"});
        auto found = repo.findById(id);
        std::cout << "CRUD add/find id=" << id << " found=" << bool(found) << '\n';
        if(found) {
            found->level="vip";
            std::cout << "CRUD update=" << repo.update(*found) << '\n';
        }
        std::cout << "CRUD remove=" << repo.remove(id)
                  << " find after remove=" << bool(repo.findById(id)) << '\n';
        int ormId = repo.add({0,"ORM demo trader","orm@example.test","basic"});
        std::cout << "ORM insert/get id=" << ormId << " found=" << bool(repo.findById(ormId)) << '\n';
        repo.remove(ormId);
        runQueries(db);
        runTransactions(db);
        std::cout << "\nFINAL traders=" << db.count<Trader>() << " orders=" << db.count<Order>() << '\n';
        return 0;
    } catch(const std::exception& ex) {
        std::cerr << "ERROR: " << ex.what() << '\n';
        return 1;
    }
}