import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request
import os

app = Flask(__name__)

current_datetime = datetime.now()
today_date = current_datetime.strftime('%d-%m-%Y')


def increment_date(date_str, days):
    month_name_mapping = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    input_date = datetime.strptime(date_str, '%d-%b-%Y')

    incremented_dates = []

    for day in range(days):
        new_date = input_date + timedelta(days=day)
        month_name = month_name_mapping[new_date.month]
        new_date_str = new_date.strftime(f'%d-{month_name}')
        incremented_dates.append(new_date_str)

    return incremented_dates


def get_data(user_input, date_input):
    global travel_date

    train_number = user_input
    api_key = os.environ["train_key"]

    start_date = date_input
    date = start_date.replace("-", "")
    date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%d %b %Y')
        if formatted_date[0] == "0":
        formatted_date = formatted_date[1:]
    formatted_date_2nd = date_obj.strftime('%d-%b-%Y')

    url = f"https://www.trainman.in/services/get-ntes-running-status/{train_number}?key=" \
          f"{api_key}&int=1&refresh=true&date={date}"

    headers = {'User-Agent': 'Chrome/91.0.4472.114'}
    response = requests.get(url=url, headers=headers)
    Data = response.json()

    current_rake_station = None
    rakes = Data['rakes']
    for Rakes in rakes:
        if Rakes['startDate'] == formatted_date:
            current_rake_station = Rakes['stations']

    station_with_halt = []
    stations_data = []
    for n in range(len(current_rake_station)):
        if current_rake_station[n]['halt'] != "00:00":
            station_with_halt.append(current_rake_station[n])

    station_with_halt.insert(0, current_rake_station[0])
    station_with_halt[0]['arrive'] = 'Start'
    station_with_halt.append(current_rake_station[-1])
    station_with_halt[-1]['depart'] = 'End'

    travel_days = station_with_halt[-1]['day']

    for n in range(len(station_with_halt)):
        station_name = station_with_halt[n].get('sname', None)
        station_code = station_with_halt[n].get('stnCode', None)
        station_day = station_with_halt[n].get('day', None)
        station_arrival = station_with_halt[n].get('arrive', None)
        station_dept = station_with_halt[n].get('depart', None)
        station_delay = station_with_halt[n].get('delayDep', None)
        station_departed_bool = station_with_halt[n].get('dep', None)
        station_arrival_bool = station_with_halt[n].get('arr', None)

        DELAY_D = station_with_halt[n].get('delayDep', None)
        if DELAY_D is not None:
            if DELAY_D >= 60:
                hours = DELAY_D // 60
                minutes = DELAY_D % 60
                DELAY_D = f"{hours} hr {minutes} min"
            else:
                DELAY_D = f"{DELAY_D} min"

        if station_delay is not None and station_delay > 0:
            station_status = f"Late by: {DELAY_D}"
        elif station_delay is not None and station_delay == 0:
            station_status = "On time"
        else:
            DELAY_d = abs(int(DELAY_D[:3]))
            station_status = f"Early by: {DELAY_d} min"

        new_dates_list = increment_date(formatted_date_2nd, travel_days)
        new_dates_list.insert(0, "XX-XX")
        print(new_dates_list)
        curr_date = None
        for Index in range(len(new_dates_list)):
            if Index == station_day:
                curr_date = new_dates_list[Index]
                break

        station_info = {'station_name': station_name, 'station_code': station_code, 'station_day': station_day,
                        'station_arrival': station_arrival, 'station_dept': station_dept, 'station_delay':
                        station_delay, 'DELAY_D': DELAY_D, 'station_status': station_status, 'curr_date': curr_date,
                        'station_departed_bool': station_departed_bool, 'station_arrival_bool': station_arrival_bool}

        stations_data.append(station_info)

    return stations_data


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/process', methods=['POST'])
def process():
    user_input = request.form['user_input']
    Date_input = request.form['Date_input']
    stations_data = get_data(user_input, Date_input)
    image_links = []
    crossed = 0

    for n, station in enumerate(stations_data):
        if station['station_departed_bool']:
            image_links.append("/static/leave.png")
            crossed = n
        elif station['station_arrival_bool'] and station['station_dept'] == 'End':
            image_links.append("/static/leave.png")
        elif not station['station_departed_bool'] and not station['station_arrival_bool']:
            image_links.append("/static/upcoming.png")
        else:
            image_links.append("/static/dot.gif")

    if today_date < Date_input:
        for n, station in enumerate(stations_data):
            if n <= crossed:
                image_links[n] = "/static/leave.png"
            if n > crossed:
                image_links[n+1] = "/static/dot.gif"
                break

    return render_template("table.html", stations_data=stations_data, image_links=image_links, user_input=user_input,
                           Date_input=Date_input)


if __name__ == '__main__':
    app.run(debug=True)
