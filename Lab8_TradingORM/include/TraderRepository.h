#pragma once
#include <optional>
#include <vector>
#include "Database.h"
class ITraderRepository {
public:
    virtual ~ITraderRepository() = default;
    virtual int add(const Trader&) = 0;
    virtual std::optional<Trader> findById(int) = 0;
    virtual std::vector<Trader> findAll() = 0;
    virtual bool update(const Trader&) = 0;
    virtual bool remove(int) = 0;
};
class SQLiteTraderRepository final : public ITraderRepository {
    Storage& db_;
public:
    explicit SQLiteTraderRepository(Storage& db) : db_(db) {}
    int add(const Trader& trader) override;
    std::optional<Trader> findById(int id) override;
    std::vector<Trader> findAll() override;
    bool update(const Trader& trader) override;
    bool remove(int id) override;
};