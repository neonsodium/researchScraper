import subprocess
import datetime
# import os
# import shutil

# file_name = "/Users/vedanths/PycharmProjects/Bankinglabs/internship_1/scraping_server/main/Pubmed/Code/pubmed_5.py"
file_name = "/var/www/html/main/Pubmed/Code/pubmed_5.py"


def get_biweekly_dates(start_year, end_year):
    biweekly_dates = []
    for year in range(start_year, end_year + 1):
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)
        current_date = start_date

        while current_date <= end_date:
            biweekly_dates.append((current_date, current_date + datetime.timedelta(days=1)))
            current_date += datetime.timedelta(days=1)

    biweekly_list = [f"{start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')}" for start_date, end_date in
                     biweekly_dates]
    return biweekly_list




def main():
    mailer_flag = 0
    keyword = input('Article Keyword: ')
    title = input('Article Title: ')
    abstract = input('Article Abstract: ')
    start_year = int(input("Start year: "))
    end_year = int(input("End year: "))

    output_path = f'/var/www/html/output/PubMed_Output_{title}_{keyword}_{abstract}_{start_year}_{end_year}.csv'
    # output_path = f'/Users/vedanths/PycharmProjects/Bankinglabs/scraping_server/output/PubMed_Output_{title}_{keyword}_{abstract}_{start_year}_{end_year}.csv'
    f = open(output_path, '+w')
    f.close()

    biweekly_list = get_biweekly_dates(start_year, end_year)

    # Loop through the arguments and execute the file for each argument
    for biweekly_date in biweekly_list:
        try:
            start_date, end_date = biweekly_date.split(" - ")
            arguments = ["python3", file_name, title, keyword, abstract, start_date, end_date, output_path]
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            try:
                stdout, stderr = process.communicate(timeout=30)  # Set the timeout value (in seconds)
            except subprocess.TimeoutExpired:
                process.terminate()  # Terminate the process if it exceeds the timeout
                stdout, stderr = process.communicate()

            exit_code = process.wait()

            if exit_code != 0:
                print(f"Error for argument: {biweekly_date}")
                print("Standard Output:", stdout)
                print("Standard Error:", stderr)
            else:
                print(f"Successfully executed for argument: {biweekly_date}")
                mailer_flag = 1
        except Exception as e:
            print(f"An error occurred for argument: {biweekly_date}")
            print(e) 
    if mailer_flag:
        python_mailer = "/var/www/html/main/Mailer/mailer_4.py"
        # python_mailer = "/Users/vedanths/PycharmProjects/Bankinglabs/scraping_server/main/Mailer/mailer_4.py"
        try:
            # Execute the Python file
            subprocess.run(["python3", python_mailer,output_path])
        except subprocess.CalledProcessError as e:
            print(f"Error executing the Python file: {e}")
        except FileNotFoundError as e:
            print(f"Python interpreter not found: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
