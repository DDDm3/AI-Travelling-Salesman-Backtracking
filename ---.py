import sys
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # Sửa import
from PyQt6 import QtCore, QtGui, QtWidgets
import time 
import copy
class Warshall:
    def __init__(self, graph, variables):
        self.graph = graph
        self.variables = variables
        self.n = len(variables)
        self.path_matrix = [[0] * self.n for _ in range(self.n)]
        self.create_path_matrix()

    def compute_shortest_paths(self):
        self.create_path_matrix()

    def get_shortest_path(self, start, end):
        city_index = {city: idx for idx, city in enumerate(self.variables)}
        return self.path_matrix[city_index[start]][city_index[end]]

    def create_path_matrix(self):
        city_index = {city: idx for idx, city in enumerate(self.variables)}

        for i in range(self.n):
            for j in range(self.n):
                self.path_matrix[i][j] = float('inf') if i != j else 0  # Khởi tạo khoảng cách ban đầu

        for city, neighbors in self.graph.items():
            for neighbor, weight in neighbors:
                self.path_matrix[city_index[city]][city_index[neighbor]] = weight

        for k in range(self.n):
            for i in range(self.n):
                for j in range(self.n):
                    self.path_matrix[i][j] = min(
                        self.path_matrix[i][j],
                        self.path_matrix[i][k] + self.path_matrix[k][j]
                    )

    def is_reachable(self, from_city, to_city):
        city_index = {city: idx for idx, city in enumerate(self.variables)}
        return self.path_matrix[city_index[from_city]][city_index[to_city]] != float('inf')

class CSPproblem:
    def __init__(self, variables, domains, graph, start, algorithm_choice='base'):
        self.variables = variables
        self.n = len(variables)
        self.domains = domains
        self.graph = graph
        self.start = start
        self.assignments = {}
        self.algorithm_choice = algorithm_choice
        self.min_cost = None
        self.min_path = []
        self.memo = {}     
           
        
    def get_neighbors_degree(self, city, path):
        # Lấy danh sách neighbors và sắp xếp dựa trên Degree Heuristic
        neighbors = self.graph.get(city, [])
        # Lưu ý là bạn đang sắp xếp theo degree (số neighbors), không phải chi phí
        
        degree_order = sorted(neighbors, key=self.priority, reverse=True)  # Ưu tiên số lượng ràng buộc cao nhất
        return degree_order
        

    def priority(self, neighbor):
        city = neighbor[0]
        return self.constraint_degree(city)

    def constraint_degree(self, city):
        return len(self.graph.get(city, []))
    
    def is_goal(self, current_city, path):
        return len(path) == self.n + 1 and current_city == self.start

    def is_consistent_constraint(self, city, path):
        return city not in path

    def get_neighbors(self, city):
        return self.graph.get(city, [])

    def assign(self, city, path):
        path.append(city)

    def unassign(self, city, path):
        path.pop()

    def forward_check(self, current_city, neighbor, path):
        remaining_domains = self.domains.copy()
        for city in self.variables:
            if city not in path and city != neighbor:
                for n, _ in self.get_neighbors(city):
                    if n == neighbor and n in remaining_domains[city]:
                        remaining_domains[city].remove(n)
                        # Nếu miền của biến nào rỗng, trả về False
                        if not remaining_domains[city]:
                            return False, remaining_domains
        return True, remaining_domains

    def revise(self, xi, xj):
        revised = False
        for x in self.domains[xi][:]:
            if not any(self.is_consistent_constraint(x, y) for y in self.domains[xj]):
                self.domains[xi].remove(x)
                revised = True
        return revised

    def apply_ac3(self):
        queue = [(xi, xj) for xi in self.domains for xj in self.domains if xi != xj]
        while queue:
            xi, xj = queue.pop(0)
            if self.revise(xi, xj):
                if not self.domains[xi]:
                    return False
                for xk in self.variables:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))
        return True

    # def select_variable_highest_degree(self, path):
    #     """Chọn biến có số lượng ràng buộc (degree) lớn nhất."""
    #     max_degree = -1
    #     selected_variable = None
    #     for variable in self.variables:
    #         if variable not in path:
    #             degree = len([neighbor for neighbor, _ in self.get_neighbors(variable) if neighbor not in path])
    #             if degree > max_degree:
    #                 max_degree = degree
    #                 selected_variable = variable
    #     return selected_variable

    def is_neighbor(self, from_city, to_city):
        """Kiểm tra nếu to_city là hàng xóm trực tiếp của from_city"""
        neighbors = [neighbor[0] for neighbor in self.graph.get(from_city, [])]
        return to_city in neighbors


    def minimum_remaining_values(self, path, invalid_cities):
        min_remaining = float('inf')
        selected_variable = None

        print(f"Debug - Current Path: {path}")  # In trạng thái đường đi hiện tại
        print(f"Debug - Invalid Cities: {invalid_cities}")  # In danh sách thành phố không khả thi

        for variable in self.variables:
            # Bỏ qua các thành phố đã trong path hoặc bị đánh dấu không khả thi
            if variable in path or variable in invalid_cities:
                continue

            # Kiểm tra nếu variable là hàng xóm trực tiếp của path[-1]
            if path and not self.is_neighbor(path[-1], variable):
                invalid_cities.add(variable)  # Đánh dấu là không khả thi
                print(f"Debug - City '{variable}' không phải là hàng xóm của '{path[-1]}'. Adding to invalid list.")
                continue

            # Nếu hợp lệ, xét số lượng giá trị còn lại (MRV)
            remaining_values = len(self.domains[variable])
            print(f"Debug - City '{variable}' is reachable. Remaining values: {remaining_values}.")
            if remaining_values < min_remaining:
                min_remaining = remaining_values
                selected_variable = variable

        print(f"Debug - Selected Variable: {selected_variable}")  # In biến được chọn cuối cùng
        return selected_variable


class Backtracking_degree:

    def __init__(self, variables, domains, graph, start, algorithm_choice):
        self.problem = CSPproblem(variables, domains, graph, start, algorithm_choice)

    def backtrack(self, current_city, path_length, path):

        print("Current City:", current_city)
        print("Path Length:", path_length)
        print("Path:", path)
        print()

        if self.problem.is_goal(current_city, path):
            if self.problem.min_cost is None or path_length < self.problem.min_cost:
                self.problem.min_cost = path_length
                self.problem.min_path = path.copy()
            return

    
        for (neighbor, distance) in self.problem.get_neighbors_degree(current_city, path):
            if self.problem.is_consistent_constraint(neighbor, path):
                self.problem.assign(neighbor, path)
                self.backtrack(neighbor, path_length + distance, path)
                self.problem.unassign(neighbor, path)

        if len(path) == self.problem.n:
            for (neighbor, distance) in self.problem.get_neighbors_degree(current_city, path):
                if neighbor == self.problem.start:
                    self.problem.assign(neighbor, path)
                    self.backtrack(neighbor, path_length + distance, path)
                    self.problem.unassign(neighbor,path)


    def solve(self):
        start_city = self.problem.start
        self.problem.assign(start_city, [start_city])
        self.backtrack(start_city, 0, [start_city])
        return self.problem.min_path, self.problem.min_cost
    
class BacktrackingWarshall:
    def __init__(self, graph, variables):
        self.warshall = Warshall(graph, variables)  # Tham chiếu đến lớp Warshall
        self.min_cost = float('inf')
        self.min_path = []


    def backtrack(self, path, current_cost):
       
        # Nếu tất cả các thành phố đã được ghé thăm, kiểm tra chi phí quay về thành phố bắt đầu
        if len(path) == len(self.warshall.variables):
            start_city = path[0]
            last_city = path[-1]
            total_cost = current_cost + self.warshall.get_shortest_path(last_city, start_city)
            if total_cost < self.min_cost:
                self.min_cost = total_cost
                self.min_path = path + [start_city]
            return

        # Lấy thành phố hiện tại
        current_city = path[-1]

        # Duyệt qua tất cả các thành phố còn lại
        for next_city in self.warshall.variables:
            if next_city not in path:
                cost_to_next = self.warshall.get_shortest_path(current_city, next_city)

                # Chỉ tiếp tục nếu chi phí hiện tại chưa vượt quá chi phí tốt nhất
                if current_cost + cost_to_next < self.min_cost:
                    # Gán giá trị (thêm thành phố vào đường đi)
                    path.append(next_city)
                    self.backtrack(path, current_cost + cost_to_next)
                    # Hủy gán giá trị (xóa thành phố khỏi đường đi)
                    path.pop()

    def solve(self, start_city):
        self.min_cost = float('inf')
        self.min_path = []
        self.backtrack([start_city], 0)
        return self.min_path, self.min_cost

class Backtracking_ac3:
    def __init__(self, variables, domains, graph, start, algorithm_choice):
        self.problem = CSPproblem(variables, domains, graph, start, algorithm_choice)
      

    def backtrack(self, path, current_cost):

      # Nếu tất cả các biến đã được gán, kiểm tra chu trình hoàn chỉnh
      if len(path) == len(self.problem.variables):
          start_city = path[0]
          last_city = path[-1]

          # Thêm chi phí quay về thành phố ban đầu
          for neighbor, cost in self.problem.get_neighbors(last_city):
              if neighbor == start_city:
                  total_cost = current_cost + cost
                  if total_cost < self.problem.min_cost:
                      self.problem.min_cost = total_cost
                      self.problem.min_path = path + [start_city]
                  return

      # Gán giá trị cho các biến còn lại
      current_city = path[-1]
      for neighbor, cost in self.problem.get_neighbors(current_city):
          if self.problem.is_consistent_constraint(neighbor, path):
              original_domains = copy.deepcopy(self.problem.domains)
              # Áp dụng AC3
              if self.problem.apply_ac3():
                  # Gán giá trị
                  path.append(neighbor)
                  self.backtrack(path, current_cost + cost)
                  # Hủy gán giá trị
                  path.pop()
              # Khôi phục miền giá trị sau khi quay lui
              self.problem.domains = original_domains

    def solve(self, start_city):
        if not self.problem.apply_ac3():
              print("AC3 thất bại. Không thể giải bài toán.")
              return None, None
        self.problem.min_cost = float('inf')
        self.problem.min_path = []
        self.backtrack([start_city], 0)
        return self.problem.min_path, self.problem.min_cost
   
class Backtracking_mrv:

    def __init__(self, variables, domains, graph, start):
        self.problem = CSPproblem(variables, domains, graph, start, algorithm_choice="mrv")
        self.visited = set()  # Lưu các trạng thái đã duyệt để tránh lặp lại
        self.start = start  # Thành phố bắt đầu
        self.warshall = Warshall(graph, variables)
      

    def backtrack(self, path, current_cost, invalid_cities, backtracked_cities, visited_states):
        current_state = (tuple(path), current_cost)

        # Kiểm tra trạng thái đã duyệt
        if current_state in visited_states:
            print(f"Debug - State {current_state} already visited, backtracking.")
            return

        # Thêm trạng thái hiện tại vào visited states
        visited_states.add(current_state)

        # Điều kiện dừng: Nếu tất cả thành phố đã được ghé thăm
        if len(path) == len(self.problem.variables):
            last_city = path[-1]
            if self.problem.is_neighbor(last_city, self.start):
                total_cost = current_cost + self.problem.warshall.get_shortest_path(last_city, self.start)
                if total_cost < self.problem.min_cost:
                    self.problem.min_cost = total_cost
                    self.problem.min_path = path + [self.start]
            return

        # Làm sạch danh sách các thành phố không hợp lệ
        invalid_cities.clear()

        # Chọn thành phố tiếp theo
        next_city = self.problem.minimum_remaining_values(path, invalid_cities.union(backtracked_cities))

        if next_city is None:
            print("Debug - No valid city found. Backtracking.")
            return

        # Gán thành phố tiếp theo
        path.append(next_city)

        # Duyệt qua các hàng xóm của thành phố
        for neighbor, cost in self.problem.get_neighbors(next_city):
            if self.problem.is_consistent_constraint(neighbor, path):
                self.backtrack(path, current_cost + cost, invalid_cities, backtracked_cities, visited_states)

        # Quay lui: Bỏ gán thành phố
        path.pop()

        # Nếu không có hàng xóm hợp lệ, thêm vào danh sách không hợp lệ
        if not any(self.problem.is_consistent_constraint(n, path) for n, _ in self.problem.get_neighbors(next_city)):
            invalid_cities.add(next_city)
            print(f"Debug - Adding '{next_city}' to invalid cities.")

    def solve(self, start_city):
        self.problem.min_cost = float('inf')
        self.problem.min_path = []
        self.visited.clear()
        invalid_cities = set()  # Tạo danh sách invalid cities ban đầu
        backtracked_cities = set()  # Các thành phố đã quay lui
        visited_states = set()
        print(f"Debug - Initial Backtracked Cities: {backtracked_cities}")
        print(f"Debug - Initial Invalid Cities: {invalid_cities}")
        self.backtrack([start_city], 0, invalid_cities, backtracked_cities, visited_states)
        
        return self.problem.min_path, self.problem.min_cost

 
class Backtracking_fc:
    
    def __init__(self, variables, domains, graph, start, algorithm_choice):
        self.problem = CSPproblem(variables, domains, graph, start, algorithm_choice)
        
    def backtrack(self, current_city, path_length, path):
       
        if self.problem.is_goal(current_city, path):
            if self.problem.min_cost is None or path_length < self.problem.min_cost:
                self.problem.min_cost = path_length
                self.problem.min_path = path.copy()
            return


        for (neighbor, distance) in self.problem.get_neighbors(current_city):
            if self.problem.is_consistent_constraint(neighbor, path):
               is_valid, remaining_domains = self.problem.forward_check(current_city,neighbor, path)
               if is_valid:
                   self.problem.assign(neighbor,path)
                   original_domains = self.problem.domains
                   self.problem.domains = remaining_domains
                   self.backtrack(neighbor,path_length + distance, path)
                   self.problem.domains = original_domains
                   self.problem.unassign(neighbor,path)
                   
        if len(path) == self.problem.n:
            for (neighbor, distance) in self.problem.get_neighbors(current_city):
                if neighbor == self.problem.start:
                    self.problem.assign(neighbor, path)
                    self.backtrack(neighbor, path_length + distance, path)
                    self.problem.unassign(neighbor,path)
        

    def solve(self):
        start_city = self.problem.start
        self.problem.assign(start_city, [start_city])
        self.backtrack(start_city, 0, [start_city])
        return self.problem.min_path, self.problem.min_cost
        
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1500, 1600)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.start = QtWidgets.QComboBox(parent=self.centralwidget)
        self.start.setGeometry(QtCore.QRect(1300, 350, 150, 30))
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.start.setFont(font)
        self.start.setObjectName("start")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.start.addItem("")
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setGeometry(QtCore.QRect(390, 10, 171, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(1340, 320, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.graph = QtWidgets.QWidget(parent=self.centralwidget)
        self.graph.setGeometry(QtCore.QRect(20, 60, 1200, 600))
        self.graph.setObjectName("graph")
        self.find = QtWidgets.QPushButton(parent=self.centralwidget)
        self.find.setGeometry(QtCore.QRect(1280, 470, 200, 40))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.find.setFont(font)
        self.find.setObjectName("find")
        self.lineEdit = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(20, 720, 1200, 50))
        self.lineEdit.setObjectName("lineEdit")
        self.label_4 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(450, 680, 131, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.label_3 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(1310, 40, 161, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.comboBox = QtWidgets.QComboBox(parent=self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(1300, 100, 150, 30))
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.comboBox.setFont(font)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.Dem_thoi_gian = QtWidgets.QLabel(parent=self.centralwidget)
        self.Dem_thoi_gian.setGeometry(QtCore.QRect(1330, 640, 100, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        self.Dem_thoi_gian.setFont(font)
        self.Dem_thoi_gian.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.Dem_thoi_gian.setMouseTracking(False)
        self.Dem_thoi_gian.setObjectName("Dem_thoi_gian")
        self.label_5 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(1300, 580, 211, 50))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(1290, 190, 181, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
  
        font = QtGui.QFont()
        font.setFamily("Arial")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1500, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        
        self.setupGraph()
        self.find.clicked.connect(self.find_path)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.start.setItemText(0, _translate("MainWindow", "NONE"))
        self.start.setItemText(1, _translate("MainWindow", "Tây Ninh"))
        self.start.setItemText(2, _translate("MainWindow", "Đồng Nai"))
        self.start.setItemText(3, _translate("MainWindow", "Sài Gòn"))
        self.start.setItemText(4, _translate("MainWindow", "Biên Hòa"))
        self.start.setItemText(5, _translate("MainWindow", "Cửu Long"))
        self.start.setItemText(6, _translate("MainWindow", "Kiên Giang"))
        self.start.setItemText(7, _translate("MainWindow", "Đà Nẵng"))
        self.start.setItemText(8, _translate("MainWindow", "Bến Tre"))
        self.start.setItemText(9, _translate("MainWindow", "Huế"))
        self.start.setItemText(10, _translate("MainWindow", "Hà Nội"))
        self.start.setItemText(11, _translate("MainWindow", "Thái Bình"))
        self.start.setItemText(12, _translate("MainWindow", "Sơn La"))
        self.start.setItemText(13, _translate("MainWindow", "Hải Phòng"))
        self.label.setText(_translate("MainWindow", "TÌM ĐƯỜNG"))
        self.label_2.setText(_translate("MainWindow", "BẮT ĐẦU"))
        self.find.setText(_translate("MainWindow", "TÌM ĐƯỜNG"))
        self.label_4.setText(_translate("MainWindow", "ĐƯỜNG ĐI"))
        self.label_3.setText(_translate("MainWindow", "PHƯƠNG PHÁP"))
        self.comboBox.setItemText(0, _translate("MainWindow", "ac3"))
        self.comboBox.setItemText(1, _translate("MainWindow", "forward_check"))
        self.comboBox.setItemText(2, _translate("MainWindow", "warshall"))
        self.comboBox.setItemText(3, _translate("MainWindow", "mrv"))
        self.comboBox.setItemText(4, _translate("MainWindow", "degree"))
        self.Dem_thoi_gian.setText(_translate("MainWindow", "00:00:00"))
        self.label_5.setText(_translate("MainWindow", "THỜI GIAN CHẠY"))
        
     
        
    def setupGraph(self):
        
            graph = {
        'Tây Ninh': [('Đồng Nai', 85), ('Sài Gòn', 26), ('Bến Tre', 40)],
        'Đồng Nai': [('Sài Gòn', 737), ('Đà Nẵng', 83), ('Tây Ninh', 85)],
        'Sài Gòn': [('Đà Nẵng', 80), ('Tây Ninh', 26), ('Bến Tre', 120), ('Đồng Nai', 77)],
        'Bến Tre': [('Kiên Giang', 96), ('Tây Ninh', 40), ('Cửu Long', 83), ('Sài Gòn', 120)],
        'Cửu Long': [('Đà Nẵng', 140), ('Bến Tre', 83), ('Hà Nội', 49), ('Biên Hòa', 25)],
        'Đà Nẵng': [('Cửu Long', 140), ('Huế', 77), ('Đồng Nai', 83), ('Sài Gòn', 80)],
        'Kiên Giang': [('Bến Tre', 96), ('Biên Hòa', 73)],
        'Huế': [('Đà Nẵng', 77), ('Thái Bình', 93), ('Hà Nội', 78)],
        'Hà Nội': [('Cửu Long', 49), ('Huế', 78), ('Sơn La', 200), ('Hà Tĩnh', 71)],
        'Thái Bình': [('Sơn La', 280), ('Huế', 93)],
        'Sơn La': [('Hà Nội', 200), ('Thái Bình', 280), ('Hải Phòng', 77)],
        'Hải Phòng': [('Sơn La', 77), ('Hà Tĩnh', 50)],
        'Hà Tĩnh': [('Hải Phòng', 50), ('Hà Nội', 71), ('Biên Hòa', 30)],
        'Biên Hòa': [('Hà Tĩnh', 30), ('Cửu Long', 25), ('Kiên Giang', 73)]
    }

            G = nx.Graph()

            for city, connections in graph.items():
                for connection in connections:
                    G.add_edge(city, connection[0], weight=connection[1])

        
            fig, ax = plt.subplots(figsize=(10, 6))
            self.canvas = FigureCanvas(fig)

        
            layout = QtWidgets.QVBoxLayout(self.graph)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.canvas)

        
            pos = nx.spring_layout(G)
        
        
            nx.draw_networkx_nodes(G, pos, node_size=2000, node_color = 'cyan')

        
            nx.draw_networkx_edges(G, pos, width=5, alpha=0.5, edge_color ='blue')

        
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")


            edge_labels = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

            self.canvas.draw()
    
    def find_path(self):
        graph = {
            'Tây Ninh': [('Đồng Nai', 85), ('Sài Gòn', 26), ('Bến Tre', 40)],
            'Đồng Nai': [('Sài Gòn', 737), ('Đà Nẵng', 83), ('Tây Ninh', 85)],
            'Sài Gòn': [('Đà Nẵng', 80), ('Tây Ninh', 26), ('Bến Tre', 120), ('Đồng Nai', 77)],
            'Bến Tre': [('Kiên Giang', 96), ('Tây Ninh', 40), ('Cửu Long', 83), ('Sài Gòn', 120)],
            'Cửu Long': [('Đà Nẵng', 140), ('Bến Tre', 83), ('Hà Nội', 49), ('Biên Hòa', 25)],
            'Đà Nẵng': [('Cửu Long', 140), ('Huế', 77), ('Đồng Nai', 83), ('Sài Gòn', 80)],
            'Kiên Giang': [('Bến Tre', 96), ('Biên Hòa', 73)],
            'Huế': [('Đà Nẵng', 77), ('Thái Bình', 93), ('Hà Nội', 78)],
            'Hà Nội': [('Cửu Long', 49), ('Huế', 78), ('Sơn La', 200), ('Hà Tĩnh', 71)],
            'Thái Bình': [('Sơn La', 280), ('Huế', 93)],
            'Sơn La': [('Hà Nội', 200), ('Thái Bình', 280), ('Hải Phòng', 77)],
            'Hải Phòng': [('Sơn La', 77), ('Hà Tĩnh', 50)],
            'Hà Tĩnh': [('Hải Phòng', 50), ('Hà Nội', 71), ('Biên Hòa', 30)],
            'Biên Hòa': [('Hà Tĩnh', 30), ('Cửu Long', 25), ('Kiên Giang', 73)]
        }

        variables = list(graph.keys())
        start = self.start.currentText()
        #domains = {city: [neighbor[0] for neighbor in neighbors if neighbor[0] != city] for city, neighbors in graph.items()}
        domains = {
            city: [neighbor[0] for neighbor in neighbors]
            for city, neighbors in graph.items()
        }

        algorithm = self.comboBox.currentText()    
         
        
        if algorithm == 'ac3':
            solver = Backtracking_ac3(variables, domains, graph, start, algorithm)
            start_time = time.time()
            path, cost = solver.solve(start)
            end_time = time.time()
            print(f"Execution Time: {end_time - start_time:.2f} seconds")
            print("CSP Minimum Path:", path)
            print("CSP Minimum Cost:", cost)
        elif algorithm =='forward_check':
            solver = Backtracking_fc(variables, domains, graph, start, algorithm)      
            start_time = time.time()
            path, cost = solver.solve()
            end_time = time.time()
            print(f"Execution Time: {end_time - start_time:.2f} seconds")
            print("CSP Minimum Path:", path)
            print("CSP Minimum Cost:", cost)
        elif algorithm =='warshall':
            solver = BacktrackingWarshall(graph, variables)      
            start_time = time.time()
            path, cost = solver.solve(start)
            end_time = time.time()
            print(f"Execution Time: {end_time - start_time:.2f} seconds")
            print("CSP Minimum Path:", path)
            print("CSP Minimum Cost:", cost)
        elif algorithm =='mrv':
            solver = Backtracking_mrv(variables, domains, graph, start)      
            start_time = time.time()
            path, cost = solver.solve(start)
            end_time = time.time()
            print(f"Execution Time: {end_time - start_time:.2f} seconds")
            print("CSP Minimum Path:", path)
            print("CSP Minimum Cost:", cost)
        elif algorithm =='degree':
            solver = Backtracking_degree(variables, domains, graph, start, algorithm)      
            start_time = time.time()
            path, cost = solver.solve()
            end_time = time.time()
            print(f"Execution Time: {end_time - start_time:.2f} seconds")
            print("CSP Minimum Path:", path)
            print("CSP Minimum Cost:", cost)
            
        self.lineEdit.setText(f'Đường đi: {path};        Chi phí: {cost}')
        self.Dem_thoi_gian.setText(f'{end_time - start_time:.4f}s')
       
       
      


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
