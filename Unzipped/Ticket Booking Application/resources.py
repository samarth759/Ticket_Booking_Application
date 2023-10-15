import jwt
#from jwt import auth_required
from jwt_trial import auth_required
from datetime import datetime, timedelta
from flask import current_app as app
from flask_caching import Cache
import time
import pandas as pd
import csv 

from flask_restful import Resource,Api,reqparse,fields,marshal_with,abort
from models import db
from models import USER,Theatre,Show,Ticket
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from tasks import *

app.config["CACHE_TYPE"] = "RedisCache"
app.config['CACHE_REDIS_HOST'] = "localhost"
app.config['CACHE_REDIS_PORT'] = 6379
app.config["CACHE_REDIS_URL"] = "redis://localhost:6379"  
app.config['CACHE_DEFAULT_TIMEOUT'] = 200

cache = Cache(app)
api=Api(app)


@app.route("/hello",methods=["GET","POST"])
def hello():
    job=just_say_hello.delay()
    print("gbjkfdg")
    return str(job),200

user_req = reqparse.RequestParser()
user_req.add_argument('name',type=str,help="name is a string")
user_req.add_argument('username',type=str,help="Username is a string")
user_req.add_argument('user_id',type=int,help="user_id is an integer")
user_req.add_argument('password',type=str,help="password is a string")

user_field={
    'user_id': fields.Integer,
    'name': fields.String,
    'username': fields.String,
    'password': fields.String,
}


theatre_req = reqparse.RequestParser()
theatre_req.add_argument('theatre_id',type=int,help="theatre_id is an integer")
theatre_req.add_argument('user_id',type=int,help="user_id is an integer")
theatre_req.add_argument('name',type=str,help="name is a string")
theatre_req.add_argument('place',type=str,help="place is a string")
theatre_req.add_argument('capacity',type=int,help="capacity is an integer")

# theatre_field={
#     'user_id': fields.Integer,
#     'theatre_id': fields.Integer,
#     'name': fields.String,
#     'place': fields.String,
#     'capacity': fields.Integer
# }

theatre_fields = {
    'user_id': fields.Integer,
    'theatre_id': fields.Integer,
    'name': fields.String,
    'place': fields.String,
    'capacity': fields.Integer,
    'trend': fields.String,
    'show_list': fields.List(fields.Nested({
        'theatre_id': fields.Integer,
        'show_id': fields.Integer,
        'name': fields.String,
        'rating': fields.Float,
        'tags': fields.String,
        'ticket_price': fields.Float,
        'num_tickets': fields.Integer,
        'datetime': fields.String
    })),
}


show_req = reqparse.RequestParser()
show_req.add_argument('show_id',type=int,help="show_id is an integer")
show_req.add_argument('theatre_id',type=int,help="theatre_id is an integer")
show_req.add_argument('name',type=str,help="name is a string")
show_req.add_argument('rating',type=float,help="rating is a float")
show_req.add_argument('tags',type=str,help="tags is a string")
show_req.add_argument('ticket_price',type=float,help="ticket_price is a float")
show_req.add_argument('num_tickets',type=int,help="num_stickets is an integer")
show_req.add_argument('datetime',type=str,help="datetime is a string")



show_field={
    'theatre_id': fields.Integer,
    'show_id': fields.Integer,
    'name': fields.String,
    'rating':fields.Float,
    'tags':fields.String,
    'ticket_price':fields.Float,
    'num_tickets':fields.Integer,
    'datetime':fields.String
}

show_field_new={
    'theatre_id': fields.Integer,
    'show_id': fields.Integer,
    'name': fields.String,
    'rating':fields.Float,
    'tags':fields.String,
    'ticket_price':fields.Float,
    'num_tickets':fields.Integer,
    'datetime':fields.String,
    'booked_tickets':fields.Integer,
    'theatre_name':fields.String
}


ticket_booking_req = reqparse.RequestParser()
ticket_booking_req.add_argument("booked_tickets", type=int, required=True, help="Number of tickets booked is required.")

ticket_booking_fields = {
    "ticket_id": fields.Integer,
    "user_id": fields.Integer,
    "show_id": fields.Integer,
    "booked_tickets": fields.Integer,
    "price": fields.Integer,
    "total": fields.Integer
}


user_rating_parser = reqparse.RequestParser()
user_rating_parser.add_argument("rate", type=float, required=True, help="Please provide a valid rating (1 to 5)")

user_rating_fields = {
    "rate": fields.Float,
}

#################################################################################################################
# USER LOGIN AND SIGNUP


class User_Login(Resource):
    # @marshal_with(user_field)
    def post(self):
        d={}
        data=user_req.parse_args()
        username=data.get("username",None)
        password=data.get("password",None)
        if username:
            if password:
                user=USER.query.filter(USER.username==username).first()
                if user:
                    if user.role=="User":
                        if user.password==password:
                            d["user"]=[user.user_id,user.name,user.username]
                            d["token"]=jwt.encode({
                                    'uid': user.user_id,
                                    'exp' : datetime.utcnow() + timedelta(minutes = 30)
                            }, app.config['SECRET_KEY'])
                            return d
                        else:
                            abort(404,message="Wrong password")
                    else:
                        abort(404,message="This username does not belong to an User")
                else:
                    abort(404,message="User does not exists! Please signup")
            else:
                abort(404,message="Please enter password")
        else:
            abort(404,message="Please enter email ID")

api.add_resource(User_Login,"/api/user_login")



class User_Signup(Resource):
    @marshal_with(user_field)
    def post(self):
        d={}
        data=user_req.parse_args()
        name=data.get("name",None)
        username=data.get("username",None)
        password=data.get("password",None)
        if name:
            if username:
                if password:
                    dup_user=USER.query.filter(USER.username==username).first()
                    if dup_user:
                        abort(404,message="User already exists")
                    else:
                        user=USER(name=name,username=username,password=password,role="User")
                        db.session.add(user)
                        db.session.commit()
                        d["user"]=data
                        d["token"]=jwt.encode(
                            {'uid': user.user_id,'exp' : datetime.utcnow() + timedelta(minutes = 30)}, app.config['SECRET_KEY']
                            )
                        return d
                else:
                    abort(404,message="Please enter password")
            else:
                abort(404,message="Please enter username")
        else:
            abort(404,message="Please enter name")


api.add_resource(User_Signup,"/api/user_signup")


##############################################################################################################
# USER DASHBOARD



class User_Dashboard(Resource):
    @auth_required
    #getting list and respective cards
    @marshal_with(theatre_fields)
    @cache.cached(timeout=4)
    def get(self,user_id=None):
        d={}
        if user_id:
            user=USER.query.filter(USER.user_id==user_id).first()
            if user:
                theatre=Theatre.query.all()
                if theatre:
                    for i in theatre:
                        show=Show.query.filter(Show.theatre_id==i.theatre_id).all()
                        i.show_list=show
                        i.user=user
                    return theatre
                else:
                    abort(404,message="no theatre found")
            else:
                abort(404,message="Invalid user id")
        else:
            abort(404,message="Enter user id")

api.add_resource(User_Dashboard,"/api/userdashboard/<int:user_id>")



##############################################################################################
# ADMIN LOGIN

class Admin_Login(Resource):
    # @marshal_with(user_field)
    def post(self):
        d={}
        data=user_req.parse_args()
        username=data.get("username",None)
        password=data.get("password",None)
        if username:
            if password:
                user=USER.query.filter(USER.username==username).first()
                if user:
                    if user.role=="Admin":
                        if user.password==password:
                            d["user"]=[user.user_id,user.name,user.username]
                            d["token"]=jwt.encode({
                                    'uid': user.user_id,
                                    'exp' : datetime.utcnow() + timedelta(minutes = 30)
                                }, app.config['SECRET_KEY'])
                            return d
                        else:
                            abort(404,message="Wrong password")
                    else:
                        abort(404,message="This user is not an Admin")
                else:
                    abort(404,message="Admin does not exists!")
                
            else:
                abort(404,message="Please enter password")
        else:
            abort(404,message="Please enter Username")
        


api.add_resource(Admin_Login,"/api/admin_login")


#####################################################################################################
# ADMIN DASHBOARD


class Dashboard(Resource):
    @auth_required
    @marshal_with(theatre_fields)
    @cache.cached(timeout=2)
    def get(self,user_id=None):
        if user_id:
            user=USER.query.filter(USER.user_id==user_id).first()
            if user:
                theatre=Theatre.query.filter(Theatre.user_id==user_id).all()
                if theatre:
                    for i in theatre:
                        show=Show.query.filter(Show.theatre_id==i.theatre_id).all()
                        i.show_list=show
                        i.user=user
                    return theatre
                else:
                    abort(404,message="no theatre found")
            else:
                abort(404,message="Invalid user id")
        else:
            abort(404,message="Enter user id")
        

api.add_resource(Dashboard,"/api/dashboard/<int:user_id>")


##################################################################################################################


class THEATRE(Resource):
    @auth_required
    #getting theatre and its details
    @marshal_with(theatre_fields)
    def get(self,user_id=None,theatre_id=None):
        if user_id:
            user=USER.query.filter(USER.user_id==user_id).first()
            if user:
                theatre=Theatre.query.filter(Theatre.user_id==user_id).all()
                if theatre:
                    for i in theatre:
                        show=Show.query.filter(Show.theatre_id==theatre_id).all()
                        i.show_list=show
                    return theatre
                else:
                    abort(404,message="no theatre found")
            else:
                abort(404,message="Invalid user id")
        else:
            abort(404,message="Enter user id")

    # adding a theatre
    @auth_required
    @marshal_with(theatre_fields)
    def post(self,user_id=None):
        data=theatre_req.parse_args()
        name=data.get("name",None)
        place=data.get("place",None)
        capacity=data.get("capacity",None)
        if name:
            if place:
                if capacity:
                    dup_theatre = Theatre.query.filter(Theatre.name == name).first()
                    if dup_theatre:
                        abort(404, message="Venue name already exists")
                    else:
                        theatre = Theatre(user_id=user_id, name=name, place=place, capacity=capacity)
                        db.session.add(theatre)
                        db.session.commit()
                        return theatre
                else:
                    abort(404, message="Capacity of the venue missing")
            else:
                abort(404, message="Place and location missing")
        else:
            abort(404, message="Venue name missing")


#editing a theatre
    @auth_required
    @marshal_with(theatre_fields)
    def put(self,user_id=None,theatre_id=None):
        data=theatre_req.parse_args()
        name=data.get("name",None)
        place=data.get("place",None)
        capacity=data.get("capacity",None)

        if name and place and capacity:
            theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
            theatre.user_id = user_id
            theatre.theatre_id = theatre_id
            if theatre:
                theatre.name=name
                theatre.place=place
                theatre.capacity=capacity
                db.session.commit()
                return data
            else:
                abort(404,message="invalid venue")

        if name:
            theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
            if theatre:
                theatre.name=name
                db.session.commit()
                return data
            else:
                abort(404,message="invalid venue")

        if place:
            theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
            if theatre:
                theatre.place=place
                db.session.commit()
                return data
            else:
                abort(404,message="invalid venue")
        
        if capacity:
            theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
            if theatre:
                theatre.capacity=capacity
                db.session.commit()
                return data
            else:
                abort(404,message="invalid venue")

        
        theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
        if theatre:
            return data
        else:
            abort(404,message="invalid venue")


#deleting a theatre and respective shows
    @auth_required
    @marshal_with(user_field)
    def delete(self,user_id=None,theatre_id=None):
        theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
        if theatre:
            show=Show.query.filter(Show.theatre_id==theatre_id).all()
            for i in show:
                db.session.delete(i)
                db.session.commit()
            db.session.delete(theatre)
            db.session.commit()
            return 'venue deleted',200
        else:
            abort(404,message="venue does not exists")

api.add_resource(THEATRE,"/api/theatre/<int:user_id>","/api/theatre/<int:user_id>/<int:theatre_id>")





######################################################################################################################




class SHOW(Resource):
    @auth_required
    #getting theatre and its details
    @marshal_with(show_field)
    def get(self,user_id=None,theatre_id=None,show_id=None):
        if user_id:
            user=USER.query.filter(USER.user_id==user_id).first()
            if user:
                theatre=Theatre.query.filter(Theatre.theatre_id==theatre_id).first()
                if theatre:
                    show=Show.query.filter(Show.show_id==show_id).first()
                    return show
                else:
                    abort(404,message="no show found")
            else:
                abort(404,message="Invalid theatre id")
        else:
            abort(404,message="Enter user id")


    #add a show
    @auth_required
    @marshal_with(show_field)
    def post(self, user_id=None, theatre_id=None):
        data = show_req.parse_args()
        name = data.get("name", None)
        rating = data.get("rating", None)
        tags = data.get("tags", None)
        ticket_price = data.get("ticket_price", None)
        num_tickets = data.get("num_tickets", None)
        datetime= data.get("datetime",None)

        if name and rating and tags and ticket_price and num_tickets and datetime:
            theatre = Theatre.query.filter_by(theatre_id=theatre_id).first()
            if not theatre:
                abort(404, message="Invalid theatre")

            existing_show = Show.query.filter(Show.datetime==datetime).first()
            if existing_show:
                abort(404, message="Show with the same name already exists in this theatre")
            
            if theatre.capacity < num_tickets:
                abort(404, message="number of available tickets can not exceeds theatre capacity")

            show = Show(theatre_id=theatre_id, name=name, rating=rating, tags=tags, ticket_price=ticket_price, num_tickets=num_tickets,datetime=datetime)
            db.session.add(show)
            db.session.commit()
            return show
        else:
            abort(404, message="Missing required show attributes")


#editing a show
    @auth_required
    @marshal_with(show_field)
    def put(self,user_id=None,theatre_id=None,show_id=None):
        data=show_req.parse_args()
        name = data.get("name", None)
        tags = data.get("tags", None)
        ticket_price = data.get("ticket_price", None)
        num_tickets = data.get("num_tickets", None)
        datetime= data.get("datetime",None)

        show=Show.query.filter(Show.show_id==show_id).first()
        if show:
            if name:
                show.name = name
            if tags:
                show.tags = tags
            if ticket_price is not None:
                show.ticket_price = ticket_price
            if num_tickets is not None:
                show.num_tickets = num_tickets
            if datetime is not None:
                show.datetime = datetime
            theatre = Theatre.query.filter_by(theatre_id=theatre_id).first()
            if theatre.capacity < num_tickets:
                abort(404, message="number of available tickets can not exceeds theatre capacity")

            db.session.commit()
            return data
        else:
            abort(404,"invalid show")



#deleting a show
    @auth_required
    @marshal_with(show_field)
    def delete(self,user_id=None,theatre_id=None,show_id=None):
        show=Show.query.filter(Show.show_id==show_id).first()
        if show:
            db.session.delete(show)
            db.session.commit()
            return 'show deleted',200
        else:
            abort(404,message="show does not exists")

api.add_resource(SHOW,"/api/show/<int:user_id>/<int:theatre_id>/<int:show_id>","/api/show/<int:user_id>/<int:theatre_id>")



#################################################################################################################################################



#ticket_booking

class TicketAPI(Resource):
    @marshal_with(ticket_booking_fields)
    def post(self,user_id=None,theatre_id=None,show_id=None,num_tickets=None):
        data = ticket_booking_req.parse_args()

        num_tickets_booked = data.get("booked_tickets")

        user = USER.query.filter(USER.user_id==user_id).first()
        if not user:
            abort(404, message="Admins are not allowed to book tickets")

        show = Show.query.filter(Show.show_id==show_id).first()
        if not show:
            abort(404, message="Show not found")

        if num_tickets_booked <= 0:
            abort(404, message="Number of tickets booked should be greater than 0")

        if show.num_tickets < num_tickets_booked:
            abort(404, message="Not enough tickets available for booking")
        
        if show.num_tickets == 0:
            abort(404, message="This show is Houseful")

        # Create a new ticket booking
        ticket = Ticket(user_id=user_id, show_id=show_id, booked_tickets=num_tickets_booked , price= show.ticket_price, total = (show.ticket_price*num_tickets_booked))
        db.session.add(ticket)
        db.session.commit()

        # Update the show's available tickets count
        show.num_tickets -= num_tickets_booked
        db.session.commit()

        return ticket

api.add_resource(TicketAPI, "/api/ticketbooking/<int:user_id>/<int:theatre_id>/<int:show_id>/<int:num_tickets>")

##################################################################################################################################

#user_bookings

class UserBookingsAPI(Resource):
    @marshal_with(show_field_new)
    def get(self, user_id=None):
        user = USER.query.get(user_id)
        if not user:
            return "Invalid user id"

        bookings = Ticket.query.filter_by(user_id=user_id).all()

        show_details = []
        for booking in bookings:
            show = Show.query.get(booking.show_id)
            if show:
                theatre = Theatre.query.filter(Theatre.theatre_id==show.theatre_id).first()
                show_dict = show.__dict__
                show_dict["booked_tickets"] = booking.booked_tickets
                show_dict["theatre_name"] = theatre.name
                show_details.append(show_dict)

        return show_details
    
api.add_resource(UserBookingsAPI,"/api/userbookings/<int:user_id>")


#####################################################################################################################
# Export for users

class User_Export_Dashboard(Resource):
    @auth_required
    #getting list and respective cards
    @marshal_with(show_field)
    #@cache.cached(timeout=2)
    def get(self,user_id=None):
        d={}
        show_list=[]
        if user_id:
            user=USER.query.filter(USER.user_id==user_id).first()
            if user:
                shows=Show.query.all()
                if shows:
                    for show in shows:
                        show_list.append({
                                "Show Name": show.name,
                                "Ratings": show.rating,
                                "Tags": show.tags,
                                "Ticket Price": show.ticket_price,
                                "Number of Tickets Available": show.num_tickets,
                                "Timings of the Show": show.datetime
                            })
                    
                    df = pd.DataFrame(show_list) 
                    df.to_csv('file_show.csv')
                    print(show_list)
                    return show_list
                else:
                    abort(404,message="no show found")
            else:
                abort(404,message="Invalid user id")
        else:
            abort(404,message="Enter user id")

api.add_resource(User_Export_Dashboard,"/api/userexportdashboard/<int:user_id>")

###################################################################################################################################
# Export for admin


class Admin_Export_Theatre(Resource):
    @marshal_with(theatre_fields)
    #@cache.cached(timeout=2)
    def get(self, user_id=None, theatre_id=None):
        d = {}
        if user_id:
            user = USER.query.filter(USER.user_id == user_id).first()
            if user:
                theatre = Theatre.query.filter(Theatre.theatre_id == theatre_id).first()
                if theatre:
                    show_list = []
                    shows = Show.query.filter(Show.theatre_id == theatre_id).all()
                    for show in shows:
                        show_list.append({
                            "name": show.name,
                            "rating": show.rating,
                            "tags": show.tags,
                            "ticket_price": show.ticket_price,
                            "num_tickets": show.num_tickets,
                            "datetime": show.datetime
                        })

                    d = {
                        "name": theatre.name,
                        "place": theatre.place,
                        "capacity": theatre.capacity,
                        "show_list": show_list
                    }
                    df = pd.DataFrame(d) 
                    df.to_csv('file_theatre.csv')
                    print(d)
                    return d
                else:
                    abort(404, message="no theatre found")
            else:
                abort(404, message="Invalid user id")
        else:
            abort(404, message="Enter user id")

api.add_resource(Admin_Export_Theatre, "/api/export_theatre/<int:user_id>/<int:theatre_id>")


###############################################################################################################################

#user_rating
class User_Rating(Resource):
    @marshal_with(user_rating_fields)
    def post(self, user_id=None, show_id=None):
        data = user_rating_parser.parse_args()
        rate = data.get("rate")

        if rate < 0 or rate > 5:
            abort(400, message="Rating should be between 0 and 5")
        if user_id:
            user = USER.query.filter_by(user_id=user_id).first()
            if user:
                show = Show.query.filter_by(show_id=show_id).first()
                if show:

                    total_sum = show.rating + rate
                    new_mean = total_sum / 2
                    new_mean = round(new_mean, 1)
                    show.rating = new_mean
                    db.session.commit()

                    return {"rate": new_mean}
                else:
                    abort(404, message="Show not found")
            else:
                abort(404, message="Invalid user id")
        else:
            abort(404, message="Enter user id")

api.add_resource(User_Rating, "/api/show/rate/<int:user_id>/<int:show_id>")

#########################################################################################################################

#searches
class SearchTheatresByLocation(Resource):
    @marshal_with(theatre_fields)
    def post(self,user_id=None):
        data = theatre_req.parse_args()
        location = data.get("place")
        if location=="":
            abort(404,message="Please enter Place and Loaction")
        theatres = Theatre.query.filter(Theatre.place.ilike(f"%{location}%")).all()
        return theatres
api.add_resource(SearchTheatresByLocation, "/api/searchtheatresbylocation")

class SearchShowsByTags(Resource):
    @marshal_with(show_field)
    def post(self):
        data = show_req.parse_args()
        tags = data.get("tags")
        if tags=="":
            abort(404,message="Please enter tags you want to search")

        shows = Show.query.filter(Show.tags.ilike(f"%{tags}%")).all()
        return shows
    
api.add_resource(SearchShowsByTags, "/api/searchshowsbytags")


class SearchShowsByRating(Resource):
    @marshal_with(show_field)
    def post(self):
        data = show_req.parse_args()
        rating = data.get("rating")
        if rating==0 or rating=='':
            abort(404,message="Please enter valid ratings ")

        shows = Show.query.filter(Show.rating >= rating).all()
        return shows
    
api.add_resource(SearchShowsByRating, "/api/searchshowsbyrating")




################################################################################################################


#summary page
class Summary(Resource):
    @marshal_with(theatre_fields)
    @auth_required
    @cache.cached(timeout=2)
    def get(self, user_id=None):
        if user_id is not None:
            user = USER.query.filter(USER.user_id == user_id).first()
            if user:
                theatres = Theatre.query.filter(Theatre.user_id == user_id).all()
                for theatre in theatres:
                    shows = Show.query.filter(Show.theatre_id == theatre.theatre_id).all()
                    theatre_tags = {}  
                    for show in shows:
                        tags = show.tags.split(",") if show.tags else []
                        for tag in tags:
                            tag = tag.strip()
                            if tag not in theatre_tags:
                                theatre_tags[tag] = 1
                            else:
                                theatre_tags[tag] += 1
                    names = list(theatre_tags.keys())
                    values = list(theatre_tags.values())
                    plt.bar(range(len(theatre_tags)), values, tick_label=names)
                    plt.savefig('project/src/assets/bargraph'+str(theatre.theatre_id)+'.png')

                    if len(shows)==0:
                        theatre.trend="Capture.png"
                    else:
                        theatre.trend='bargraph'+str(theatre.theatre_id)+'.png'
                    db.session.commit()

                return theatres
            else:
                abort(404, message="Invalid user id")
        else:
            abort(404, message="Enter user id")

api.add_resource(Summary,"/api/summary/<int:user_id>")



#################################################################################################################


class Logout(Resource):
    #@auth_required
    @marshal_with(user_field)
    def get(self,user_id=None):
        if user_id:
            user=USER.query.filter(USER.user_id==user_id).first()
            if user:
                return user
            else:
                abort(404,message="invalid user id")
        else:
            abort(404,message="enter user id")

api.add_resource(Logout,"/api/logout/<int:user_id>")



@app.route('/huehue')
@cache.cached(timeout=50)
def testingcache():
    time.sleep(10)
    return "done"