import argparse
import ast
import subprocess
import sys
import os
import re
import logging
import json
from datetime import datetime, timedelta
import csv
from time import sleep
import shutil

"""
Usage example:
python3 bktest_script.py --strategy SampleStrategy --config config.json --start-date 20200101 --end-date 20240925 --period 30
"""


# Define the function to calculate date ranges
def calculate_date_ranges(start_date, end_date, period, split):
    date_ranges = []
    current_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")

    if split:
        # Calculate the total number of days in the period
        total_days = (end_date - current_date).days

        # Calculate the length of each sub-period
        sub_period_length = total_days // split

        # Split the period into equal sub-periods
        for i in range(split):
            sub_start_date = current_date + timedelta(days=i * sub_period_length)
            sub_end_date = sub_start_date + timedelta(days=sub_period_length)
            date_ranges.append((sub_start_date.strftime("%Y%m%d"), sub_end_date.strftime("%Y%m%d")))
        
        # Adjust the last sub-period to end at the specified end_date
        date_ranges[-1] = (date_ranges[-1][0], end_date.strftime("%Y%m%d"))

    else:
        # Use the provided period to generate date ranges
        while current_date < end_date:
            date_ranges.append((current_date.strftime("%Y%m%d"), (current_date + timedelta(days=period)).strftime("%Y%m%d")))
            current_date += timedelta(days=period)

    return date_ranges

def run_backtest(start_date, end_date, strategy_name, config, execution_time):
    # Construct the command with the specified date range
    command = f"freqtrade backtesting --timerange {start_date}-{end_date} --timeframe 5m --timeframe-detail 1m --strategy {strategy_name} -c {config} --cache none"
    
    # Execute the command
    logging.info(f"Running backtest for period {start_date} to {end_date}...")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    
    # Check for errors
    # if stderr:
    #     logging.error(f"Error occurred while running backtest: {stderr}")
        # It should return None if error, but there is always error (freqtrade feature apparently)
    
    # Return the stdout which contains the backtest results
    return stdout

def in_venv():
    if sys.prefix != sys.base_prefix:
        logging.info("Virtual environment is activated.")
    else:
        logging.error("Virtual environment is not activated. Run script from virtual environment.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Backtest strategy by periods")
    parser.add_argument("--strategy", type=str, help="Strategy name", required=True)
    parser.add_argument("--config", type=str, help="Config filename", required=True)
    parser.add_argument("--start-date", type=str, help="Start date (yyyymmdd)", required=True)
    parser.add_argument("--end-date", type=str, help="End date (yyyymmdd)", required=True)
    parser.add_argument("--period", type=int, help="Period in days for backtest (default: 30)", default=30)
    parser.add_argument("--split", type=int, help="Split whole period for N equal periods (optional)")
    args = parser.parse_args()
    return args

def setup_logging(execution_time):
    logs_directory = os.path.join('bktest_script_files', execution_time)
    os.makedirs(logs_directory, exist_ok=True)

    script_logfile = os.path.join(logs_directory, 'script_execution.log')
    logging.basicConfig(filename=script_logfile, level=logging.INFO, format='%(asctime)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

def handler(strategy, config, start_date, end_date, period, split, execution_time):
    logs_directory = os.path.join('bktest_script_files', execution_time)
    log_file = os.path.join(logs_directory, f"backtest_{execution_time}.log")
    logging.info(f"log_file: {log_file}")
    
    # Calculate date ranges for backtesting
    date_ranges = calculate_date_ranges(start_date, end_date, period, split)
    
    # Process backtest results and store them in a CSV file
    result_csv = os.path.join(logs_directory, f"results_{strategy}_{config[:-5]}_{execution_time}.csv")
    
    # Write the results to a CSV file
    with open(result_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Strategy", "Total Trades", "Profit Mean", "Profit Median", "Profit Total", "Profit Total Long", "Profit Total Short", "Profit Factor", "CAGR", "Sortino", "Sharpe", "Calmar", "Wins", "Losses", "Winrate", "Holding Avg", "Max Drawdown Account", "Max Relative Drawdown", "Max Drawdown", "Med_Profit/Med_Draw"])
        writer.writerow(["Median", "=MEDIAN(B4:B100)", "=MEDIAN(C4:C100)", "=MEDIAN(D4:D100)", "=MEDIAN(E4:E100)", "=MEDIAN(F4:F100)", "=MEDIAN(G4:G100)", "=MEDIAN(H4:H100)", "=MEDIAN(I4:I100)", "=MEDIAN(J4:J100)", "=MEDIAN(K4:K100)", "=MEDIAN(L4:L100)", "=MEDIAN(M4:M100)", "=MEDIAN(N4:N100)", "=MEDIAN(O4:O100)", "=MEDIAN(P4:P100)", "=MEDIAN(Q4:Q100)", "=MEDIAN(R4:R100)", "=MAX(Q4:R100)", "=E2/R2"])
        writer.writerow(["Average", "=AVERAGE(B4:B100)", "=AVERAGE(C4:C100)", "=AVERAGE(D4:D100)", "=AVERAGE(E4:E100)", "=AVERAGE(F4:F100)", "=AVERAGE(G4:G100)", "=AVERAGE(H4:H100)", "=AVERAGE(I4:I100)", "=AVERAGE(J4:J100)", "=AVERAGE(K4:K100)", "=AVERAGE(L4:L100)", "=AVERAGE(M4:M100)", "=AVERAGE(N4:N100)", "=AVERAGE(O4:O100)", "=AVERAGE(P4:P100)", "=AVERAGE(Q4:Q100)", "=AVERAGE(R4:R100)"])        
    
    # Run backtest for each date range
    for i, (start, end) in enumerate(date_ranges):
        backtest_result = run_backtest(start, end, strategy, config, execution_time)
        logging.info(f"backtest_result: {backtest_result}")
        sleep(1)
        
        # Define the directory where backtest results are stored
        backtest_results_directory = "./user_data/backtest_results"
        
        # Get the latest backtest result filename from .last_result.json
        with open(os.path.join(backtest_results_directory, '.last_result.json'), 'r') as f:
            last_result_data = json.load(f)
            latest_backtest_filename = last_result_data.get('latest_backtest')
        # Construct the full path to the latest backtest result file
        latest_backtest_path = os.path.join(backtest_results_directory, latest_backtest_filename)
        logging.info(f"latest_backtest_path: {latest_backtest_path}")
        logging.info(f"backtest_result: {backtest_result}")
        
        if backtest_result:
            process_backtest_results(latest_backtest_path, result_csv, strategy, start, end)
        else:
            logging.error("Backtest failed.")

def process_backtest_results(backtest_result_path, output_csv_path, strategy_name, start_date, end_date):
    try:
        with open(backtest_result_path, 'r') as file:
            backtest_data = json.load(file)
        # logging.info(f"backtest_data: {backtest_data}")
    except FileNotFoundError:
        logging.error(f"Backtest result file not found at path: {backtest_result_path}")
        return
    except json.decoder.JSONDecodeError:
        logging.error(f"Error decoding JSON in file: {backtest_result_path}")
        return

    # Check if 'strategy' key exists in backtest_data
    if 'strategy' in backtest_data:
        # Log the keys of the 'strategy' dictionary
        # logging.info(f"Keys in backtest_data['strategy']: {backtest_data['strategy'][strategy_name].keys()}")
        
        # Extract required data from backtest results
        result_dict = {
            "strategy": {
                strategy_name: {
                    "total_trades": backtest_data['strategy'][strategy_name]["total_trades"],
                    "profit_mean": backtest_data['strategy'][strategy_name]["profit_mean"],
                    "profit_median": backtest_data['strategy'][strategy_name]["profit_median"],
                    "profit_total": backtest_data['strategy'][strategy_name]["profit_total"],
                    "profit_total_long": backtest_data['strategy'][strategy_name]["profit_total_long"],
                    "profit_total_short": backtest_data['strategy'][strategy_name]["profit_total_short"],
                    "profit_factor": backtest_data['strategy'][strategy_name]["profit_factor"],
                    "cagr": backtest_data['strategy'][strategy_name]["cagr"],
                    "sortino": backtest_data['strategy'][strategy_name]["sortino"],
                    "sharpe": backtest_data['strategy'][strategy_name]["sharpe"],
                    "calmar": backtest_data['strategy'][strategy_name]["calmar"],
                    "wins": backtest_data['strategy'][strategy_name]["wins"],
                    "losses": backtest_data['strategy'][strategy_name]["losses"],
                    "winrate": backtest_data['strategy'][strategy_name]["winrate"],
                    "holding_avg": backtest_data['strategy'][strategy_name]["holding_avg"],
                    "max_drawdown_account": backtest_data['strategy'][strategy_name]["max_drawdown_account"],
                    "max_relative_drawdown": backtest_data['strategy'][strategy_name]["max_relative_drawdown"]
                }
            }
        }
        
        # Write the results to a CSV file
        with open(output_csv_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            row_values = [f"{start_date}-{end_date}"]
            for key in result_dict["strategy"][strategy_name]:
                row_values.append(result_dict["strategy"][strategy_name][key])
            writer.writerow(row_values)

    else:
        logging.error("Key 'strategy' not found in backtest data.")

def main():
    # Get current date and time for logs directory naming
    execution_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Setup logging
    setup_logging(execution_time)

    # Check if virtual environment is activated
    in_venv()

    # Parse arguments
    args = parse_arguments()
    strategy = args.strategy
    config = args.config
    start_date = args.start_date
    end_date = args.end_date
    period = getattr(args, 'period', 30)
    split = getattr(args, 'split', None)

    handler(strategy, config, start_date, end_date, period, split, execution_time)

if __name__ == "__main__":
    main()