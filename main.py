import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request
import os

app = Flask(__name__)

current_datetime = datetime.now()
today_date = current_datetime.strftime('%d-%m-%Y')


def format_date(date):
    formatted_date = date.strftime("%d %b %Y") 
    internal_date = date.strftime("%Y%m%d") 
    return formatted_date, internal_date


def generate_dates():
    today = datetime.today()
    future_dates = []
    past_dates = []

    for i in range(3, 0, -1):
        past_date = today - timedelta(days=i)
        past_dates.append(format_date(past_date))

    todays_date = format_date(today)
    return past_dates + [todays_date]


def get_data(user_input, date_input):
    global travel_date

    train_number = user_input
    api_key = os.environ["train_key"]
    date_obj = datetime.strptime(date_input, "%Y%m%d")
    selected_date = date_obj.strftime("%d %b %Y")
    if selected_date[0] == "0":
        selected_date = selected_date[1:]
    url = f"https://www.trainman.in/services/get-ntes-running-status/{train_number}?key=" \
          f"{api_key}&int=1&refresh=true&date={selected_date}"

    headers = {'User-Agent': 'Chrome/91.0.4472.114'}
    response = requests.get(url=url, headers=headers)
    Data = response.json()
    if Data['message'] == 'OK':
        current_rake_station = None
        train_name = Data['train_name']
        rakes = Data['rakes']

        for Rakes in rakes:
            if Rakes['startDate'] == selected_date:
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

            station_info = {'station_name': station_name, 'station_code': station_code, 'station_day': station_day,
                            'station_arrival': station_arrival, 'station_dept': station_dept, 'station_delay':
                                station_delay, 'DELAY_D': DELAY_D, 'station_status': station_status,
                            'station_departed_bool': station_departed_bool, 'station_arrival_bool': station_arrival_bool,
                            'train_name': train_name, }

            stations_data.append(station_info)

        return stations_data
    else:
        request_status = False
        return request_status


@app.route('/')
def index():
    display_dates = generate_dates()
    return render_template('home.html', available_dates=display_dates)


@app.route('/process', methods=['POST'])
def process():
    user_input = request.form['user_input']
    Date_input = request.form['date_input']
    formatted_date = datetime.strptime(Date_input, "%Y%m%d")
    start_date = formatted_date.strftime("%d %b %Y")

    stations_data = get_data(user_input, Date_input)
    if not stations_data:
        display_dates = generate_dates()
        return render_template('error.html', available_dates=display_dates)
    else:
        train_name = stations_data[0]['train_name']
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
                    image_links[n] = "/static/dot.gif"
                    break

        return render_template("table.html", stations_data=stations_data, image_links=image_links, user_input=user_input,
                               start_date=start_date, train_name=train_name)


if __name__ == '__main__':
    app.run(debug=True)

