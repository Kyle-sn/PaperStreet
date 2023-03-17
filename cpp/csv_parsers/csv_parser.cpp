#include "csv.h"
#include <iostream>
#include <fstream>

int main(){
  io::CSVReader<6> in("../test_data.csv");
  
  in.read_header(io::ignore_extra_column, "account", "start_balance", "pnl", "broker commission", "exchange fees", "end_balance");
  std::string account; double start_balance, pnl, broker_commission, exchange_fees, end_balance; 
  
  std::ofstream outfile("output.csv");
  outfile << "account,start_balance,pnl,end_balance" << std::endl;

  while(in.read_row(account, start_balance, pnl, broker_commission, exchange_fees, end_balance)){
     outfile << account << "," << start_balance << "," << pnl << "," << end_balance << std::endl;
  }
}