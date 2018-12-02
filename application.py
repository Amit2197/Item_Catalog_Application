#!/usr/bin/env python3

from flask import Flask, session, \
    render_template, jsonify, request, redirect, url_for, flash
from sqlalchemy import create_engine, asc

from sqlalchemy.orm import sessionmaker
import json
import random
from database_setup import Restaurant, Base, MenuItem, User
import string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests
from flask import make_response
import httplib2

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json',
         'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON APIs to view Restaurant Information
@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/JSON/')
@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


# Show all restaurants
@app.route('/')
@app.route('/restaurants/')
def showCatalogs():
    restaurants = session.query(Restaurant).all()
    items = session.query(MenuItem).order_by(MenuItem.id.desc()).limit(5)
    return render_template('publicrestaurants.html',
                           restaurants=restaurants, items=items)


@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/<path:restaurant_name>/')
def showRestaurantsItem(restaurant_name, restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    restaurants = session.query(Restaurant).all()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant.id).order_by(MenuItem.id.desc())
    quantity = items.count()
    return render_template('restaurantsmenu.html',
                           restaurants=restaurants,
                           items=items, restaurant=restaurant,
                           quantity=quantity)


@app.route('/restaurants/<int:restaurant_id>/'
           '<path:restaurant_name>/<int:menu_id>/')
@app.route('/restaurants/<int:restaurant_id>/'
           '<path:restaurant_name>/<int:menu_id>/<path:menu_name>/')
def showMenuItems(restaurant_id, menu_id, restaurant_name, menu_name):
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    return render_template('restaurantmenuitem.html', item=item)


# Task 1: Create route for newMenuItem function here

@app.route('/restaurants/<int:user_id>/info')
def showUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return render_template('userinfo.html', user=user)


@app.route('/restaurants/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newcategory = Restaurant(name=request.form['name'],
                                 user_id=login_session['user_id'])
        session.add(newcategory)
        session.commit()
        flash("new Category %s created!" % request.form['name'])
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCategory.html', )


@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editCategory(restaurant_id):
    editedRestaurant = session.query(Restaurant) \
        .filter_by(id=restaurant_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            flash("Category %s has been edited" % request.form['name'])
            return redirect(url_for('showCatalogs'))
    else:
        return render_template('editCategory.html',
                               restaurant=editedRestaurant)


@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(restaurant_id):
    deleteRestaurant = session.query(Restaurant) \
        .filter_by(id=restaurant_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        session.delete(deleteRestaurant)
        session.commit()
        flash("Category has been deleted")
        return redirect(
            url_for('showCatalogs'))
    else:
        return render_template('deleteCategory.html',
                               restaurant=deleteRestaurant)


@app.route('/restaurant/<int:restaurant_id>/'
           'menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'],
                           description=request.form['description'],
                           price=request.form['price'],
                           course=request.form['course'],
                           picture=request.form['picture'],
                           restaurant_id=restaurant_id,
                           user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New Item %s has been created" % request.form['name'])
        return redirect(url_for('showCatalogs'))
    else:
        restaurants = session.query(Restaurant).all()
        return render_template('newmenuitem.html', restaurants=restaurants)


# Task 2: Create route for editMenuItem function here


@app.route('/restaurants/<int:restaurant_id>/'
           'menu/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['name']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        if request.form['picture']:
            editedItem.course = request.form['picture']
        if login_session['user_id']:
            editedItem.user_id = login_session['user_id']
        session.add(editedItem)
        session.commit()
        flash("Item %s has been updated" % request.form['name'])
        return redirect(url_for('showCatalogs'))
    else:

        return render_template('editmenuitem.html',
                               restaurant_id=restaurant_id,
                               menu_id=menu_id, item=editedItem)


# Task 3: Create a route for deleteMenuItem function here


@app.route("/restaurants/<int:restaurant_id>/"
           "menu/<int:menu_id>/delete/", methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Item has been deleted")
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete)

# Create anti-forgery state token
@app.route('/login')
def login():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# google connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;' \
              'border-radius: 150px;-webkit-border-radius: ' \
              '150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash(" You are Successfully disconnected.")
        return redirect('/restaurants/')
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# This only happens when project.py is called directly:
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='localhost', port=8000)
