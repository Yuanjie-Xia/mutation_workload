from locust import HttpUser, task, between
import random
from pandas import read_csv

users = random.randint(1, 99)
category = random.randint(2, 6)
page = random.randint(1, 5)
product = random.randint(7, 506)
ratio = read_csv("ratio.csv")


class TeaStoreEvents(HttpUser):
    wait_time = between(1, 1)

    @task(ratio[0])
    def check_server_status(self):
        self.client.get("/tools.descartes.teastore.webui/status")

    @task(ratio[1])
    def check_user_profile(self):
        self.client.get("/tools.descartes.teastore.webui/profile")

    @task(ratio[2])
    def check_database_setup(self):
        self.client.get("/tools.descartes.teastore.webui/database")

    @task(ratio[3])
    def home(self):
        self.client.get("/tools.descartes.teastore.webui/")

    @task(ratio[4])
    def login_page(self):
        self.client.get("/tools.descartes.teastore.webui/login")

    @task(ratio[5])
    def login_action(self):
        self.client.post("/tools.descartes.teastore.webui/loginAction",
                         json={'username': users, 'password': 'password'})

    @task(ratio[6])
    def log_out(self):
        self.client.post("/tools.descartes.teastore.webui/loginAction", json={'logout': ''})

    @task(ratio[7])
    def list_products(self):
        self.client.get("/tools.descartes.teastore.webui/category",
                        json={'category': category, 'page': page})

    @task(ratio[8])
    def look_at_product(self):
        self.client.get("/tools.descartes.teastore.webui/product", json={'id': product})

    @task(ratio[9])
    def adjust_view_count(self):
        self.client.post("/tools.descartes.teastore.webui/category",
                         json={'page': 1, 'category': category, 'number': 30})

    @task(ratio[10])
    def add_product2cart(self):
        self.client.post("/tools.descartes.teastore.webui/cartAction",
                         json={'addToCart': '', 'productid': product})

    @task(ratio[11])
    def check_shopping_cart(self):
        self.client.get("/tools.descartes.teastore.webui/cart")

    @task(ratio[12])
    def place_an_order(self):
        self.client.post("/tools.descartes.teastore.webui/order")