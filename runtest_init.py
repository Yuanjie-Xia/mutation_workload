from locust import HttpUser, task, between
import random
from pandas import read_csv
import main

users = random.randint(1, 99)
category = random.randint(2, 6)
page = random.randint(1, 5)
product = random.randint(7, 506)
# ratio = read_csv("ratio.csv")
i = 0


class TeaStoreEvents1(HttpUser):
    wait_time = between(1, 1)

    @task
    def check_server_status(self):
        self.client.get("/tools.descartes.teastore.webui/status")

    @task
    def check_user_profile(self):
        self.client.get("/tools.descartes.teastore.webui/profile")

    @task
    def check_database_setup(self):
        self.client.get("/tools.descartes.teastore.webui/database")

    @task
    def home(self):
        self.client.get("/tools.descartes.teastore.webui/")

    @task
    def login_page(self):
        self.client.get("/tools.descartes.teastore.webui/login")

    @task
    def login_action(self):
        self.client.post("/tools.descartes.teastore.webui/loginAction",
                         json={'username': users, 'password': 'password'})

    @task
    def log_out(self):
        self.client.post("/tools.descartes.teastore.webui/loginAction", json={'logout': ''})

    @task
    def list_products(self):
        self.client.get("/tools.descartes.teastore.webui/category",
                        json={'category': category, 'page': page})

    @task
    def look_at_product(self):
        self.client.get("/tools.descartes.teastore.webui/product", json={'id': product})

    @task
    def adjust_view_count(self):
        self.client.post("/tools.descartes.teastore.webui/category",
                         json={'page': 1, 'category': category, 'number': 30})

    @task
    def add_product2cart(self):
        self.client.post("/tools.descartes.teastore.webui/cartAction",
                         json={'addToCart': '', 'productid': product})

    @task
    def check_shopping_cart(self):
        self.client.get("/tools.descartes.teastore.webui/cart")

    @task
    def place_an_order(self):
        self.client.post("/tools.descartes.teastore.webui/order")
