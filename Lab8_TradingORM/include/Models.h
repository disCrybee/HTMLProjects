#pragma once
#include <string>
struct Trader {
    int id = 0;
    std::string name;
    std::string email;
    std::string level;
};
struct Order {
    int id = 0;
    int traderId = 0;
    std::string symbol;
    std::string side;
    int quantity = 0;
    double price = 0.0;
    std::string status;
};