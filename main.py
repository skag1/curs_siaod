import datetime
import random
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkcalendar import DateEntry

# --- Константы ---
BUS_OPERATION_START = datetime.time(6, 0)
BUS_OPERATION_END = datetime.time(3, 0)
AM_PEAK_HOUR_START = datetime.time(7, 0)
AM_PEAK_HOUR_END = datetime.time(9, 0)
PM_PEAK_HOUR_START = datetime.time(17, 0)
PM_PEAK_HOUR_END = datetime.time(19, 0)
ROUTE_DURATION_MIN = 10
ROUTE_DURATION_MAX = 15

DRIVER_TYPE_A_MAX_HOURS = 8
DRIVER_TYPE_A_LUNCH_TIME = 60
DRIVER_TYPE_B_MAX_HOURS = 12
DRIVER_TYPE_B_BREAK_TIME = 15
DRIVER_TYPE_B_BREAK_PERIOD = 120
DRIVER_TYPE_B_EXTENDED_BREAK = 40

ROUTE_TIME_MINIMUM = 65
ROUTE_TIME_MAXIMUM = 75
DAILY_PASSENGER_FLOW = 1000
PEAK_HOUR_PASSENGER_PERCENTAGE = 0.7



# --- Параметры генетического алгоритма ---
GENETIC_POPULATION_SIZE = 50
GENETIC_MAX_GENERATIONS = 100
GENETIC_MUTATION_CHANCE = 0.1

# --- Дни недели ---
WORKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOLIDAY_NAMES = ["Saturday", "Sunday"]



# --- Структуры данных ---
class BusDriver:
    def __init__(self, driver_type, id):
        self.type = driver_type
        self.bus_schedule = []
        self.total_work_time = datetime.timedelta()
        self.last_break = datetime.datetime.combine(datetime.date.min, BUS_OPERATION_START)
        self.id = id

    def __repr__(self):
        return f"BusDriver(id={self.id}, type={self.type}, bus_schedule={len(self.bus_schedule)} shifts, worktime = {self.total_work_time})"



class BusRoute:
    def __init__(self, start_time, route_time, driver_id):
        self.start_time = start_time
        self.end_time = start_time + datetime.timedelta(minutes=route_time)
        self.driver_id = driver_id

    def __repr__(self):
        return f"BusRoute(start_time={self.start_time.strftime('%H:%M')}, end_time={self.end_time.strftime('%H:%M')}, driver_id={self.driver_id})"



class BusSchedule:
    def __init__(self):
        self.routes = []
        self.drivers = []

    def add_route(self, bus_route):
        self.routes.append(bus_route)

    def add_driver(self, bus_driver):
        self.drivers.append(bus_driver)

    def calculate_metrics(self):
        peak_routes = 0
        for bus_route in self.routes:
            if (
                (bus_route.start_time.time() >= AM_PEAK_HOUR_START and bus_route.start_time.time() < AM_PEAK_HOUR_END) or
                (bus_route.start_time.time() >= PM_PEAK_HOUR_START and bus_route.start_time.time() < PM_PEAK_HOUR_END)
                ):
              peak_routes += 1
        unique_drivers = len(self.drivers)
        total_routes = len(self.routes)
        return total_routes, peak_routes, unique_drivers


# --- Проверка на час пик ---
def is_peak_hour(time):
    return (time >= AM_PEAK_HOUR_START and time < AM_PEAK_HOUR_END) or (time >= PM_PEAK_HOUR_START and time < PM_PEAK_HOUR_END)

# --- Проверка выходного дня ---
def is_weekend(date):
   return date.strftime('%A') in HOLIDAY_NAMES


# --- Прямой алгоритм создания расписания ---
def build_direct_schedule(num_buses, num_drivers_a, num_drivers_b, current_date):
    bus_schedule = BusSchedule()
    drivers_a = []
    drivers_b = []
    current_bus_time = datetime.datetime.combine(current_date, BUS_OPERATION_START)

    # Создание водителей типа A
    for i in range(num_drivers_a):
        drivers_a.append(BusDriver('A', f'A{i+1}'))
    # Создание водителей типа B
    for i in range(num_drivers_b):
       drivers_b.append(BusDriver('B', f'B{i+1}'))


    available_drivers_a = list(drivers_a)
    available_drivers_b = list(drivers_b)
    
    
    while current_bus_time < datetime.datetime.combine(current_date, datetime.time(23, 59)):
        route_time = random.randint(ROUTE_TIME_MINIMUM, ROUTE_TIME_MAXIMUM)
        if is_peak_hour(current_bus_time.time()) and not is_weekend(current_date): # Час пик в будни
           
            for _ in range(int(num_buses*PEAK_HOUR_PASSENGER_PERCENTAGE)):  # 70% маршрутов в часы пик
                if available_drivers_a:
                    bus_driver = available_drivers_a[0]
                    # Проверка, может ли водитель выполнить смену (8 часов)
                    if bus_driver.total_work_time + datetime.timedelta(minutes=route_time) <= datetime.timedelta(hours=DRIVER_TYPE_A_MAX_HOURS):
                        bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                        bus_schedule.add_route(bus_route)
                        bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                    else:
                         available_drivers_a.pop(0)
                         continue
                elif available_drivers_b:
                    bus_driver = available_drivers_b[0]
                    
                    # Проверка, нужно ли дать перерыв
                    if bus_driver.total_work_time >= datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD) and bus_driver.last_break <= current_bus_time - datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD):
                        break_start_time = current_bus_time
                        break_end_time = current_bus_time + datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                        bus_driver.bus_schedule.append((break_start_time, break_end_time, 'break'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                        bus_driver.last_break = break_end_time
                        current_bus_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                        continue # Перерыв
                    else:
                        bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                        bus_schedule.add_route(bus_route)
                        bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                        
                        
                else:
                    break
        else: # Остальное время (30% в будни и все время в выходные)
            
            passenger_percent = 1 - PEAK_HOUR_PASSENGER_PERCENTAGE if not is_weekend(current_date) else 1
            for _ in range(int(num_buses * passenger_percent)):
               if available_drivers_a:
                   bus_driver = available_drivers_a[0]
                   
                   # Проверка, может ли водитель выполнить смену (8 часов)
                   if bus_driver.total_work_time + datetime.timedelta(minutes=route_time) <= datetime.timedelta(hours=DRIVER_TYPE_A_MAX_HOURS):
                        bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                        bus_schedule.add_route(bus_route)
                        bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                   else:
                        available_drivers_a.pop(0)
                        continue
               elif available_drivers_b:
                   bus_driver = available_drivers_b[0]
                   
                   # Проверка, нужно ли дать перерыв
                   if bus_driver.total_work_time >= datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD) and bus_driver.last_break <= current_bus_time - datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD):
                        break_start_time = current_bus_time
                        break_end_time = current_bus_time + datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)

                        bus_driver.bus_schedule.append((break_start_time, break_end_time, 'break'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                        bus_driver.last_break = break_end_time
                        current_bus_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                        continue # Перерыв
                   else:
                        bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                        bus_schedule.add_route(bus_route)
                        bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
               else:
                    break

        current_bus_time += datetime.timedelta(minutes=route_time + random.randint(ROUTE_DURATION_MIN, ROUTE_DURATION_MAX))

    # Добавляем всех водителей в расписание
    bus_schedule.drivers.extend(drivers_a)
    bus_schedule.drivers.extend(drivers_b)
    return bus_schedule



# --- Генерация случайного расписания для генетического алгоритма ---
def create_random_schedule(num_buses, num_drivers_a, num_drivers_b, current_date):
    bus_schedule = BusSchedule()
    drivers = []
    for i in range(num_drivers_a):
        drivers.append(BusDriver('A', f'A{i+1}'))
    for i in range(num_drivers_b):
        drivers.append(BusDriver('B', f'B{i+1}'))
    
    current_bus_time = datetime.datetime.combine(current_date, BUS_OPERATION_START)
    
    while current_bus_time < datetime.datetime.combine(current_date, datetime.time(23, 59)):
        route_time = random.randint(ROUTE_TIME_MINIMUM, ROUTE_TIME_MAXIMUM)
        if is_peak_hour(current_bus_time.time()) and not is_weekend(current_date): # Час пик в будни
            for _ in range(int(num_buses * PEAK_HOUR_PASSENGER_PERCENTAGE)):
                if drivers:
                    bus_driver = random.choice(drivers)
                    if bus_driver.type == 'A' and bus_driver.total_work_time + datetime.timedelta(minutes=route_time) <= datetime.timedelta(hours=DRIVER_TYPE_A_MAX_HOURS) :
                         bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                         bus_schedule.add_route(bus_route)
                         bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                         bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                    elif bus_driver.type == 'B':
                        
                        if bus_driver.total_work_time >= datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD) and bus_driver.last_break <= current_bus_time - datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD):
                            break_start_time = current_bus_time
                            break_end_time = current_bus_time + datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                            bus_driver.bus_schedule.append((break_start_time, break_end_time, 'break'))
                            bus_driver.total_work_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                            bus_driver.last_break = break_end_time
                            current_bus_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                            continue
                        else:
                            bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                            bus_schedule.add_route(bus_route)
                            bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                            bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                    else:
                      drivers.remove(bus_driver)
                      continue
                else:
                    break
        else: # Остальное время (30% в будни и все время в выходные)
            passenger_percent = 1 - PEAK_HOUR_PASSENGER_PERCENTAGE if not is_weekend(current_date) else 1
            for _ in range(int(num_buses * passenger_percent)):
               if drivers:
                  bus_driver = random.choice(drivers)

                  if bus_driver.type == 'A' and bus_driver.total_work_time + datetime.timedelta(minutes=route_time) <= datetime.timedelta(hours=DRIVER_TYPE_A_MAX_HOURS) :
                        bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                        bus_schedule.add_route(bus_route)
                        bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                        bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                  elif bus_driver.type == 'B':
                        if bus_driver.total_work_time >= datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD) and bus_driver.last_break <= current_bus_time - datetime.timedelta(minutes=DRIVER_TYPE_B_BREAK_PERIOD):
                            break_start_time = current_bus_time
                            break_end_time = current_bus_time + datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                            bus_driver.bus_schedule.append((break_start_time, break_end_time, 'break'))
                            bus_driver.total_work_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                            bus_driver.last_break = break_end_time
                            current_bus_time += datetime.timedelta(minutes=DRIVER_TYPE_B_EXTENDED_BREAK)
                            continue
                        else:
                            bus_route = BusRoute(current_bus_time, route_time, bus_driver.id)
                            bus_schedule.add_route(bus_route)
                            bus_driver.bus_schedule.append((bus_route.start_time, bus_route.end_time, 'bus_route'))
                            bus_driver.total_work_time += datetime.timedelta(minutes=route_time)
                  else:
                        drivers.remove(bus_driver)
                        continue
               else:
                    break
        current_bus_time += datetime.timedelta(minutes=route_time + random.randint(ROUTE_DURATION_MIN, ROUTE_DURATION_MAX))

    bus_schedule.drivers.extend(drivers)
    return bus_schedule



# --- Функция оценки качества расписания для генетического алгоритма ---
def assess_schedule_fitness(bus_schedule):
    total_routes, peak_routes, unique_drivers = bus_schedule.calculate_metrics()
    return  total_routes - unique_drivers*0.1


# --- Функция скрещивания расписаний для генетического алгоритма ---
def merge_schedules(schedule1, schedule2):
    split_point = random.randint(0, min(len(schedule1.routes), len(schedule2.routes)))
    child_schedule = BusSchedule()
    child_schedule.routes = schedule1.routes[:split_point] + schedule2.routes[split_point:]

    split_point = random.randint(0, min(len(schedule1.drivers), len(schedule2.drivers)))
    child_schedule.drivers = schedule1.drivers[:split_point] + schedule2.drivers[split_point:]
    return child_schedule


# --- Функция мутации расписания для генетического алгоритма ---
def alter_schedule(bus_schedule):
    if random.random() < GENETIC_MUTATION_CHANCE:
      if bus_schedule.routes:
        index_route_mutate = random.randint(0, len(bus_schedule.routes)-1)
        new_start_time = bus_schedule.routes[index_route_mutate].start_time + datetime.timedelta(minutes=random.randint(-30,30))
        if new_start_time > datetime.datetime.combine(datetime.date.min, BUS_OPERATION_START) and new_start_time < datetime.datetime.combine(datetime.date.min, BUS_OPERATION_END) + datetime.timedelta(days=1):
            bus_schedule.routes[index_route_mutate] = BusRoute(new_start_time, random.randint(ROUTE_TIME_MINIMUM, ROUTE_TIME_MAXIMUM), bus_schedule.routes[index_route_mutate].driver_id)
      if bus_schedule.drivers:
        index_driver_mutate = random.randint(0, len(bus_schedule.drivers) - 1)
        bus_schedule.drivers[index_driver_mutate].type = random.choice(['A', 'B'])
    return bus_schedule



# --- Генетический алгоритм ---
def optimize_schedule_genetically(num_buses, num_drivers_a, num_drivers_b, current_date):
    population = [create_random_schedule(num_buses, num_drivers_a, num_drivers_b, current_date) for _ in range(GENETIC_POPULATION_SIZE)]

    for generation in range(GENETIC_MAX_GENERATIONS):
        population.sort(key=assess_schedule_fitness, reverse=True)
        parents = population[:GENETIC_POPULATION_SIZE // 2]


        offspring = []
        for i in range(0, len(parents), 2):
            if i+1 < len(parents):
                child1 = merge_schedules(parents[i], parents[i+1])
                child2 = merge_schedules(parents[i+1], parents[i])
                offspring.append(alter_schedule(child1))
                offspring.append(alter_schedule(child2))
            else:
                 offspring.append(alter_schedule(parents[i]))

        population = parents + offspring
        population.sort(key=assess_schedule_fitness, reverse=True)
        population = population[:GENETIC_POPULATION_SIZE]

    return population[0]



# --- Запись расписания в CSV-файл ---
def save_schedule_to_csv(straight_schedule, genetic_schedule, output_file_name, current_date):
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Algorithm', 'BusDriver ID', 'BusSchedule'])  # Заголовки
        
        for bus_schedule, algorithm_name in [(straight_schedule, "Straight"), (genetic_schedule, "Genetic")]:
          for bus_driver in bus_schedule.drivers:
            shift_details = ""
            for start, end, type in bus_driver.bus_schedule:
              start_datetime = start
              end_datetime = end
              if type == 'bus_route':
                  shift_details += f"Маршрут: {start_datetime.strftime('%Y-%m-%d %H:%M')}-{end_datetime.strftime('%Y-%m-%d %H:%M')}, "
              elif type == 'break':
                  shift_details += f"Перерыв: {start_datetime.strftime('%Y-%m-%d %H:%M')}-{end_datetime.strftime('%Y-%m-%d %H:%M')}, "
            shift_details = shift_details.rstrip(", ")
            writer.writerow([algorithm_name, bus_driver.id, shift_details])


# --- Запись сравнения результатов в CSV-файл ---
def save_comparison_to_csv(straight_metrics, genetic_metrics, output_file_name):
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Metric', 'Straight Algorithm', 'Genetic Algorithm'])
        writer.writerow(['Total Routes', straight_metrics[0], genetic_metrics[0]])
        writer.writerow(['Peak Routes', straight_metrics[1], genetic_metrics[1]])
        writer.writerow(['Unique Drivers', straight_metrics[2], genetic_metrics[2]])


# --- Отображение расписания в таблице ---
def render_schedule_table(straight_schedule, genetic_schedule, schedule_table_widget, current_date):
    for item in schedule_table_widget.get_children():
        schedule_table_widget.delete(item)
    
    schedule_data = []
    
    for bus_schedule, algorithm_name in [(straight_schedule, "Прямой"), (genetic_schedule, "Генетический")]:
      for bus_driver in bus_schedule.drivers:
          driver_schedules = []
          for start, end, type in bus_driver.bus_schedule:
             driver_schedules.append((start, end, type))
          
          shift_details = ""
          total_work_time = 0
          total_break_time = 0
          
          for start, end, type in driver_schedules:
            if type == 'bus_route':
              total_work_time += (end - start).total_seconds() / 60
              shift_details += f"Маршрут: {start.strftime('%H:%M')}-{end.strftime('%H:%M')}, "
            elif type == 'break':
              total_break_time += (end - start).total_seconds() / 60
              shift_details += f"Перерыв: {start.strftime('%H:%M')}-{end.strftime('%H:%M')}, "
            
          shift_details = shift_details.rstrip(", ")
          
          
          schedule_data.append((algorithm_name, bus_driver.id, shift_details, f"{int(total_work_time)} мин", f"{int(total_break_time)} мин"))

    schedule_table_widget.heading("Algorithm", text="Алгоритм")
    schedule_table_widget.heading("BusDriver ID", text="Водитель")
    schedule_table_widget.heading("BusSchedule", text="Расписание")
    schedule_table_widget.heading("Work Time", text="Время работы")
    schedule_table_widget.heading("Break Time", text="Время перерыва")


    for algorithm, driver_id, shifts, work_time, break_time in schedule_data:
       schedule_table_widget.insert("", "end", values=[algorithm, driver_id, shifts, work_time, break_time])
       schedule_table_widget.column("Algorithm", width=100, anchor='center')
       schedule_table_widget.column("BusDriver ID", width=80, anchor='center')
       schedule_table_widget.column("BusSchedule", width=400, anchor='w')
       schedule_table_widget.column("Work Time", width=100, anchor='center')
       schedule_table_widget.column("Break Time", width=100, anchor='center')


# --- Функция запуска алгоритмов и отображения результатов ---
def run_and_show_schedules():
    try:
        num_buses = int(buses_entry.get())
        num_drivers_a = int(drivers_a_entry.get())
        num_drivers_b = int(drivers_b_entry.get())
        selected_date = date_entry.get_date()
    
        straight_schedule = build_direct_schedule(num_buses, num_drivers_a, num_drivers_b, selected_date)
        genetic_schedule = optimize_schedule_genetically(num_buses, num_drivers_a, num_drivers_b, selected_date)

        straight_metrics = straight_schedule.calculate_metrics()
        genetic_metrics = genetic_schedule.calculate_metrics()

        for item in schedule_table.get_children():
            schedule_table.delete(item)

        render_schedule_table(straight_schedule, genetic_schedule, schedule_table, selected_date)

        performance_metrics_label.config(
            text=f"Прямой: Маршрутов={straight_metrics[0]}, Маршрутов в пик={straight_metrics[1]}, Водителей={straight_metrics[2]} "
                 f"Генетический: Маршрутов={genetic_metrics[0]}, Маршрутов в пик={genetic_metrics[1]}, Водителей={genetic_metrics[2]}"
        )
        save_comparison_to_csv(straight_metrics, genetic_metrics, 'comparison_results.csv')
    except ValueError as e:
        performance_metrics_label.config(text=f"Ошибка: {e}")


# --- Функция сохранения расписания в файл ---
def save_schedule_to_file():
    output_file_name = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV файлы", "*.csv")])
    if output_file_name:
        num_buses = int(buses_entry.get())
        num_drivers_a = int(drivers_a_entry.get())
        num_drivers_b = int(drivers_b_entry.get())
        selected_date = date_entry.get_date()
        straight_schedule = build_direct_schedule(num_buses, num_drivers_a, num_drivers_b, selected_date)
        genetic_schedule = optimize_schedule_genetically(num_buses, num_drivers_a, num_drivers_b, selected_date)
        save_schedule_to_csv(straight_schedule, genetic_schedule, output_file_name, selected_date)

        performance_metrics_label.config(text=f"Расписание сохранено в файл: {output_file_name}")


# --- Создание основного окна ---
root = tk.Tk()
root.title("Генератор расписания автобусов")
root.geometry("1000x600")

# --- Стилизация ---
style = ttk.Style()
style.theme_use("winnative")  # Устанавливаем тему winnative

# --- Рамка для ввода данных ---
input_frame = ttk.LabelFrame(root, text="Введите данные", padding=10)
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=2)

ttk.Label(input_frame, text="Количество автобусов:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
buses_entry = ttk.Entry(input_frame, width=10)
buses_entry.insert(0, "8")
buses_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

ttk.Label(input_frame, text="Количество водителей (Тип A):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
drivers_a_entry = ttk.Entry(input_frame, width=10)
drivers_a_entry.insert(0, "10")
drivers_a_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

ttk.Label(input_frame, text="Количество водителей (Тип B):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
drivers_b_entry = ttk.Entry(input_frame, width=10)
drivers_b_entry.insert(0, "5")
drivers_b_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

ttk.Label(input_frame, text="Выберите дату:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
date_entry = DateEntry(input_frame, width=12, background="white", foreground="black", borderwidth=2,
                       year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day)
date_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

# --- Кнопки ---
button_frame = ttk.Frame(root, padding=10)
button_frame.grid(row=1, column=0, columnspan=2, pady=10)

run_button = ttk.Button(button_frame, text="Сгенерировать расписание", command=run_and_show_schedules)
run_button.grid(row=0, column=0, padx=10)

save_button = ttk.Button(button_frame, text="Сохранить расписание", command=save_schedule_to_file)
save_button.grid(row=0, column=1, padx=10)

# --- Таблица для отображения расписания ---
table_frame = ttk.LabelFrame(root, text="Сводка расписания", padding=10)
table_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

schedule_table = ttk.Treeview(table_frame, columns=("Algorithm", "BusDriver ID", "BusSchedule", "Work Time", "Break Time"), show="headings")
schedule_table.heading("Algorithm", text="Алгоритм")
schedule_table.heading("BusDriver ID", text="Водитель")
schedule_table.heading("BusSchedule", text="Расписание")
schedule_table.heading("Work Time", text="Время работы")
schedule_table.heading("Break Time", text="Время перерыва")
schedule_table.pack(fill=tk.BOTH, expand=True)

# --- Текст для вывода метрик ---
metrics_frame = ttk.Frame(root, padding=10)
metrics_frame.grid(row=3, column=0, columnspan=2, pady=10)

performance_metrics_label = ttk.Label(metrics_frame, text="Здесь отобразятся метрики.", font=("Arial", 12), foreground="black")
performance_metrics_label.pack()

root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

root.mainloop()
