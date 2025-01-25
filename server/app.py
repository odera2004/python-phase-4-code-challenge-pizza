from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# FETCH ALL RESTAURANTS
@app.route('/restaurants')
def get_all_restaurants():
    restaurants = []
    for restaurant in Restaurant.query.all():
        restaurant_dict = {
           "address" : restaurant.address,
           "id": restaurant.id,
           "name": restaurant.name
           }
        restaurants.append(restaurant_dict)

    response = make_response(jsonify(restaurants), 200)
    return response

# FETCH RESTAURANT BY ID
@app.route("/restaurants/<int:id>")
def get_restaurant_by_id(id):
    restaurant = Restaurant.query.filter_by(id=id).first()

    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    restaurant_data = {
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address,
        "restaurant_pizzas": []
    }

    for pizza in restaurant.restaurant_pizzas:
        pizza_data = {
            "id": pizza.id,
            "pizza": {
                "id": pizza.pizza.id,
                "name": pizza.pizza.name,
                "ingredients": pizza.pizza.ingredients
            },
            "pizza_id": pizza.pizza.id,
            "price": pizza.price,
            "restaurant_id": pizza.restaurant.id
        }
        restaurant_data["restaurant_pizzas"].append(pizza_data)

    return jsonify(restaurant_data)

# DELETE RESTAURANT
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)

    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    

    RestaurantPizza.query.filter_by(restaurant_id=id).delete()
    db.session.delete(restaurant)
    db.session.commit()

    return "", 204

# FETCH ALL PIZZAS
@app.route("/pizzas")
def get_all_pizzas():
    pizzas = Pizza.query.all()
    pizzas_data = [{
        "id": pizza.id,
        "ingredients": pizza.ingredients,
        "name": pizza.name
    } for pizza in pizzas]
    return jsonify(pizzas_data)

# CREATE NEW RESTAURANT PIZZAS
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizzas():
    data = request.get_json()

    restaurant_id = data.get('restaurant_id')
    pizza_id = data.get('pizza_id')
    price = data.get('price')

    errors = []

    if price is None:
        errors.append("Pizza price is required.")
    if pizza_id is None:
        errors.append("Pizza ID is required.")
    if restaurant_id is None:
        errors.append("Restaurant ID is required.")

    if errors:
        return jsonify({"errors": errors}), 400

    pizza = db.session.get(Pizza, pizza_id)
    if not pizza:
        errors.append(f"Pizza with ID {pizza_id} does not exist.")

    restaurant = db.session.get(Restaurant, restaurant_id)
    if not restaurant:
        errors.append(f"Restaurant with ID {restaurant_id} does not exist.")

    if errors:
        return jsonify({"errors": errors}), 400

    try:
        restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(restaurant_pizza)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"errors": ["validation errors"]}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": ["An error occurred while creating the RestaurantPizza."]}), 500

    response_data = {
        "id": restaurant_pizza.id,
        "pizza": {
            "id": pizza.id,
            "ingredients": pizza.ingredients,
            "name": pizza.name
        },
        "pizza_id": restaurant_pizza.pizza_id,
        "price": restaurant_pizza.price,
        "restaurant": {
            "address": restaurant.address,
            "id": restaurant.id,
            "name": restaurant.name
        },
        "restaurant_id": restaurant_pizza.restaurant_id
    }

    return jsonify(response_data), 201


if __name__ == "_main_":
    app.run(port=5555, debug=True)