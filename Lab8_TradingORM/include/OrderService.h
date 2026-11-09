#pragma once
#include "Database.h"
#include <vector>
class OrderService {
    Storage& db_;
public:
    explicit OrderService(Storage& db) : db_(db) {}
    int add(const Order& order) { return db_.insert(order); }
    std::vector<Order> all() { return db_.get_all<Order>(); }
};