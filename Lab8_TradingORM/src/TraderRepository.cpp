#include "TraderRepository.h"
int SQLiteTraderRepository::add(const Trader& trader) { return db_.insert(trader); }
std::optional<Trader> SQLiteTraderRepository::findById(int id) { return db_.get_optional<Trader>(id); }
std::vector<Trader> SQLiteTraderRepository::findAll() { return db_.get_all<Trader>(); }
bool SQLiteTraderRepository::update(const Trader& trader) {
    if (!findById(trader.id)) return false;
    db_.update(trader);
    return true;
}
bool SQLiteTraderRepository::remove(int id) {
    if (!findById(id)) return false;
    db_.remove<Trader>(id);
    return true;
}